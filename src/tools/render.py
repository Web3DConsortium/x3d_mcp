"""X3DOM HTML page rendering tool.

Wraps X3D scene content in a browser-viewable HTML page that loads X3DOM
from CDN. Handles X3D-to-X3DOM tag-case and attribute-case conversion
plus namespace stripping required by the HTML5 parser.

Adapted from generation.py in https://github.com/niknarra/x3d-mcp by
Nikhil Narra and Nicholas Polys (Virginia Tech / Web3D Consortium).
"""

import functools
import http.server
import os
import tempfile
import threading
from pathlib import Path

from lxml import etree

from mcp.server.fastmcp import FastMCP, Image

from x3d_utils.source import load_x3d_source


_X3DOM_CDN_CSS = "https://www.x3dom.org/download/1.8.2/x3dom.css"
_X3DOM_CDN_JS = "https://www.x3dom.org/download/1.8.2/x3dom.js"
# X_ITE is the render engine: unlike X3DOM it renders HAnim and X3D 4.0
# PhysicalMaterial (PBR), and it actually draws geometry under headless
# swiftshader (X3DOM only clears the background there).
_XITE_CDN_JS = "https://cdn.jsdelivr.net/npm/x_ite@latest/dist/x_ite.min.js"

# Software-GL flags so headless Chromium renders WebGL without a real GPU.
_RENDER_ARGS = [
    "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist", "--no-sandbox", "--hide-scrollbars",
]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler that doesn't spam stderr."""

    def log_message(self, *args):
        pass


def _serve_dir(directory: str):
    """Serve `directory` over loopback on an ephemeral port. Returns (httpd, port).

    X_ITE fetches the .x3d via XHR, which CORS blocks over file://, so we serve
    the scene over http://127.0.0.1 -- the same path the standalone viewer uses.
    """
    handler = functools.partial(_QuietHandler, directory=directory)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def _ensure_full_x3d(text: str) -> str:
    """Wrap a bare scene fragment in a minimal X3D document if needed."""
    s = text.strip()
    first_tag = s.split(">", 1)[0].lower()
    if s.startswith("<?xml") or "<x3d" in first_tag:
        return s
    body = s if first_tag.startswith("<scene") else f"<Scene>{s}</Scene>"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<X3D profile="Immersive" version="4.0">\n' + body + '\n</X3D>\n')


def _xite_page(width: int, height: int, src: str = "scene.x3d") -> str:
    """A minimal X_ITE page that loads `src` (relative to the served directory)."""
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f'<script src="{_XITE_CDN_JS}"></script>'
        '<style>html,body{margin:0;background:#0a0a0c}'
        f'x3d-canvas,canvas{{width:{width}px;height:{height}px;display:block}}</style>'
        f'</head><body><x3d-canvas src="{src}"></x3d-canvas></body></html>'
    )


async def _shoot(serve_dir: str, page_name: str, width: int, height: int,
                 wait_ms: int) -> bytes:
    """Serve `serve_dir` over loopback and screenshot its `page_name` via X_ITE."""
    from playwright.async_api import async_playwright

    httpd, port = _serve_dir(serve_dir)
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(args=_RENDER_ARGS)
            try:
                page = await browser.new_page(viewport={"width": width, "height": height})
                await page.goto(f"http://127.0.0.1:{port}/{page_name}",
                                wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(wait_ms)       # X_ITE: fetch CDN + draw
                try:
                    png = await page.locator("canvas").first.screenshot(timeout=8000)
                except Exception:
                    png = await page.screenshot()
            finally:
                await browser.close()
    finally:
        httpd.shutdown()
    return png


async def _render_xite_async(text: str, width: int, height: int, wait_ms: int) -> bytes:
    """Render inline X3D to PNG via X_ITE (scene written to a temp dir)."""
    full = _ensure_full_x3d(text)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "scene.x3d").write_text(full, encoding="utf-8")
        (d / "index.html").write_text(_xite_page(width, height), encoding="utf-8")
        return await _shoot(td, "index.html", width, height, wait_ms)


async def _render_xite_path_async(x3d_path: str, width: int, height: int,
                                  wait_ms: int) -> bytes:
    """Render an X3D *file* by serving its own directory, so relative assets
    (textures, inlined .x3d, etc.) resolve the same way they do in a browser."""
    p = Path(x3d_path).expanduser().resolve()
    page = p.parent / f"._x3d_render_{os.getpid()}.html"
    page.write_text(_xite_page(width, height, src=p.name), encoding="utf-8")
    try:
        return await _shoot(str(p.parent), page.name, width, height, wait_ms)
    finally:
        page.unlink(missing_ok=True)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _indent_content(content: str, spaces: int) -> str:
    prefix = " " * spaces
    lines = content.strip().split("\n")
    return "\n".join(prefix + line if line.strip() else line for line in lines)


def _element_to_x3dom_html(el: etree._Element, depth: int = 0) -> str:
    """Recursively convert an lxml element to X3DOM-friendly HTML.

    X3DOM runs inside the browser's HTML5 parser, which lowercases tag
    and attribute names and does not honor self-closing tags on non-void
    elements. This serializer normalises accordingly and strips XML
    namespace declarations / prefixed attributes.
    """
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        tag = tag.split("}", 1)[1]
    tag = tag.lower()

    attrs = []
    for attr_name, attr_val in el.attrib.items():
        if attr_name.startswith("{") or ":" in attr_name:
            continue
        # Escape for HTML attribute context -- MFString values (e.g.
        # NavigationInfo type='"EXAMINE" "ANY"') contain literal quotes.
        attr_val = attr_val.replace("&", "&amp;").replace('"', "&quot;")
        attrs.append(f'{attr_name.lower()}="{attr_val}"')

    indent = "    " * depth
    attr_str = (" " + " ".join(attrs)) if attrs else ""

    children = list(el)
    if children:
        inner = "\n".join(
            _element_to_x3dom_html(child, depth + 1) for child in children
        )
        return f"{indent}<{tag}{attr_str}>\n{inner}\n{indent}</{tag}>"

    text = (el.text or "").strip()
    if text:
        return f"{indent}<{tag}{attr_str}>{text}</{tag}>"
    return f"{indent}<{tag}{attr_str}></{tag}>"


def _local_tag(el: etree._Element) -> str:
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _extract_scene_content(x3d_content: str) -> str:
    """Extract <Scene> children from an X3D document and convert to X3DOM HTML.

    If the input is a full X3D document, parse it, find the Scene, and
    serialize each child as X3DOM HTML. If the input is already a raw
    fragment, return it as-is (assumed pre-formatted).
    """
    stripped = x3d_content.strip()

    if not stripped.startswith("<?xml") and not stripped.startswith("<X3D"):
        return _indent_content(stripped, 12)

    try:
        parser = etree.XMLParser(
            remove_blank_text=True, remove_comments=True, remove_pis=True
        )
        tree = etree.fromstring(stripped.encode(), parser)
    except etree.XMLSyntaxError:
        return _indent_content(stripped, 12)

    scene_el = None
    if _local_tag(tree) == "Scene":
        scene_el = tree
    else:
        for child in tree.iter():
            if _local_tag(child) == "Scene":
                scene_el = child
                break

    if scene_el is None:
        return _indent_content(stripped, 12)

    parts = [_element_to_x3dom_html(child, depth=0) for child in scene_el]
    return _indent_content("\n".join(parts), 12)


def _x3dom_page(
    content: str,
    title: str = "X3DOM Scene",
    width: str = "800px",
    height: str = "600px",
    show_stats: bool = False,
    show_log: bool = False,
) -> str:
    """Wrap X3D content in a complete X3DOM HTML page."""
    scene_content = _extract_scene_content(content)
    stats_attr = ' showStat="true"' if show_stats else ""
    log_attr = ' showLog="true"' if show_log else ""
    title_safe = _escape_html(title)

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title_safe}</title>
    <link rel="stylesheet" href="{_X3DOM_CDN_CSS}">
    <script src="{_X3DOM_CDN_JS}"></script>
    <style>
        body {{
            margin: 0;
            font-family: sans-serif;
            background: #1a1a2e;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }}
        h1 {{
            color: #e0e0e0;
            margin-bottom: 16px;
        }}
        x3d {{
            border: 1px solid #333;
        }}
    </style>
</head>
<body>
    <h1>{title_safe}</h1>
    <x3d width="{width}" height="{height}"{stats_attr}{log_attr}>
        <scene>
{scene_content}
        </scene>
    </x3d>
</body>
</html>"""


def _x3dom_starter(
    title: str = "X3DOM Scene",
    width: str = "800px",
    height: str = "600px",
) -> str:
    """Return a starter X3DOM HTML page with a small example scene."""
    scene_content = (
        '            <viewpoint description="Default View" position="0 0 10"></viewpoint>\n'
        '            <directionallight direction="0 -1 -1" intensity="0.8"></directionallight>\n'
        '            <transform>\n'
        '                <shape>\n'
        '                    <appearance>\n'
        '                        <material diffusecolor="0.8 0.2 0.2"></material>\n'
        '                    </appearance>\n'
        '                    <box size="2 2 2"></box>\n'
        '                </shape>\n'
        '            </transform>'
    )
    return _x3dom_page(scene_content, title=title, width=width, height=height)


def register(mcp: FastMCP):

    @mcp.tool()
    def x3dom_page(
        content: str,
        title: str = "X3DOM Scene",
        width: str = "800px",
        height: str = "600px",
        show_stats: bool = False,
        show_log: bool = False,
    ) -> str:
        """Wrap X3D scene content in a standalone X3DOM HTML page for browser viewing.

        Accepts either a full X3D XML document (will extract the <Scene> children)
        or a pre-formatted X3DOM fragment (will be embedded as-is). Tag and
        attribute names are lowercased and self-closing tags are expanded to
        match what the HTML5 parser expects.

        Args:
            content: X3D XML (full document or scene fragment).
            title: Page title.
            width: x3d element width (e.g. "800px", "100%").
            height: x3d element height (e.g. "600px", "100vh").
            show_stats: Show X3DOM frame stats overlay.
            show_log: Show X3DOM log panel.
        """
        return _x3dom_page(content, title, width, height, show_stats, show_log)

    @mcp.tool()
    async def render_image(
        content: str = "",
        path: str = "",
        width: int = 720,
        height: int = 540,
        wait_ms: int = 6000,
        save_path: str = "",
    ):
        """Render an X3D scene to a PNG image and return it so you can SEE the result.

        This closes the author -> validate -> RENDER loop: a scene can pass both
        validators and still be visually wrong (off-camera, unlit, mis-scaled).
        Renders with X_ITE in headless Chromium (software WebGL) -- X_ITE draws
        HAnim humanoids and PhysicalMaterial (PBR) that X3DOM cannot.

        Tip: if the image is blank, the usual causes are no/!bound Viewpoint, no
        light, or geometry outside the view -- not a render failure. Add a
        Viewpoint and a DirectionalLight and re-render. If it's still blank, bump
        wait_ms (X_ITE fetches its library from a CDN and needs a moment to draw).

        When `path` is given, the file's own directory is served, so relative
        assets (textures, inlined .x3d) resolve as they do in a browser.

        Args:
            content: X3D XML (full document or scene fragment), inline.
            path: Path to an X3D file to render instead of inline content.
                  Provide exactly one of `content` or `path`.
            width: Render width in pixels.
            height: Render height in pixels.
            wait_ms: Milliseconds to wait for X_ITE to initialise and draw.
            save_path: Optional path to also write the PNG to disk.
        """
        try:
            text = load_x3d_source(content, path)   # validates exactly-one-of
        except ValueError as exc:
            return f"Input error: {exc}"
        try:
            import playwright.async_api  # noqa: F401
        except ImportError:
            return (
                "render_image needs Playwright (one-time setup):\n"
                "  pip install playwright && python -m playwright install chromium\n"
                "Until then, use x3dom_page(content) and open the HTML in a browser."
            )
        try:
            if path:
                png = await _render_xite_path_async(path, width, height, wait_ms)
            else:
                png = await _render_xite_async(text, width, height, wait_ms)
        except Exception as exc:
            return f"Render failed: {exc}"
        if save_path:
            Path(save_path).expanduser().write_bytes(png)
        return Image(data=png, format="png")

    @mcp.tool()
    async def render_current_scene(width: int = 720, height: int = 540,
                                   wait_ms: int = 6000, save_path: str = ""):
        """Render the current granular (in-memory) scene to a PNG you can inspect.

        The granular-mode counterpart of render_image -- build with create_node/
        add_child, then SEE the result before declaring done. Uses X_ITE.

        Args:
            width: Render width in pixels.
            height: Render height in pixels.
            wait_ms: Milliseconds to wait for X_ITE to initialise and draw.
            save_path: Optional path to also write the PNG to disk.
        """
        from tools.granular import _scene
        try:
            import playwright.async_api  # noqa: F401
        except ImportError:
            return (
                "render needs Playwright (one-time setup):\n"
                "  pip install playwright && python -m playwright install chromium"
            )
        try:
            png = await _render_xite_async(_scene.to_xml(), width, height, wait_ms)
        except Exception as exc:
            return f"Render failed: {exc}"
        if save_path:
            Path(save_path).expanduser().write_bytes(png)
        return Image(data=png, format="png")

    @mcp.tool()
    def x3dom_starter(
        title: str = "X3DOM Scene",
        width: str = "800px",
        height: str = "600px",
    ) -> str:
        """Return a starter X3DOM HTML page with a simple example scene.

        Useful as a known-good baseline to verify the X3DOM CDN, page chrome,
        and viewpoint defaults render correctly in a browser.

        Args:
            title: Page title.
            width: x3d element width.
            height: x3d element height.
        """
        return _x3dom_starter(title, width, height)
