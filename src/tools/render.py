"""X3DOM HTML page rendering tool.

Wraps X3D scene content in a browser-viewable HTML page that loads X3DOM
from CDN. Handles X3D-to-X3DOM tag-case and attribute-case conversion
plus namespace stripping required by the HTML5 parser.

Adapted from generation.py in https://github.com/niknarra/x3d-mcp by
Nikhil Narra and Nicholas Polys (Virginia Tech / Web3D Consortium).
"""

from lxml import etree

from mcp.server.fastmcp import FastMCP


_X3DOM_CDN_CSS = "https://www.x3dom.org/download/1.8.2/x3dom.css"
_X3DOM_CDN_JS = "https://www.x3dom.org/download/1.8.2/x3dom.js"


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

    Comment, processing-instruction, and entity nodes have a non-string
    `el.tag` (lxml exposes it as a Cython function such as etree.Comment);
    these are skipped because they have no X3DOM equivalent.
    """
    tag = el.tag
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
        tag = tag.split("}", 1)[1]
    tag = tag.lower()

    attrs = []
    for attr_name, attr_val in el.attrib.items():
        if attr_name.startswith("{") or ":" in attr_name:
            continue
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
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
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
        parser = etree.XMLParser(remove_blank_text=True)
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
