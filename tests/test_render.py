"""Tests for the X3DOM rendering tool.

Mirrors the 7 X3DOM tests in
https://github.com/niknarra/x3d-mcp/blob/main/tests/test_generation.py
(Nikhil Narra, Nicholas Polys -- Virginia Tech / Web3D Consortium).
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tools.render import _x3dom_page, _x3dom_starter


def test_basic_page():
    html = _x3dom_page("<shape><box></box></shape>", title="Test")
    assert "x3dom.js" in html
    assert "x3dom.css" in html
    assert "<x3d" in html
    assert "<scene>" in html
    assert "box" in html
    assert "<title>Test</title>" in html


def test_from_full_x3d_document():
    from x3d.x3d import X3D, Scene, Viewpoint, Shape, Box

    model = X3D(
        profile="Interchange", version="4.1",
        Scene=Scene(children=[
            Viewpoint(description="Source View", position=(0, 0, 10)),
            Shape(geometry=Box()),
        ]),
    )
    x3d_xml = model.XML()

    html = _x3dom_page(x3d_xml, title="Converted")
    assert "x3dom.js" in html
    assert "viewpoint" in html.lower()
    assert "<title>Converted</title>" in html


def test_custom_dimensions():
    html = _x3dom_page("<box></box>", width="100%", height="100vh")
    assert "100%" in html
    assert "100vh" in html


def test_show_stats():
    html = _x3dom_page("<box></box>", show_stats=True)
    assert 'showStat="true"' in html


def test_show_log():
    html = _x3dom_page("<box></box>", show_log=True)
    assert 'showLog="true"' in html


def test_html_escaping_in_title():
    html = _x3dom_page("<box></box>", title='<script>alert("xss")</script>')
    title_inner = html.split("<title>")[1].split("</title>")[0]
    assert "<script>" not in title_inner


def test_starter_generates_complete_page():
    html = _x3dom_starter("Starter")
    assert "<!DOCTYPE html>" in html
    assert "x3dom.js" in html
    assert "<scene>" in html
    assert "box" in html
    assert "material" in html
    assert "directionallight" in html.lower()


# ---- helpers that don't need a browser ----

def test_ensure_full_x3d_wraps_fragment():
    from tools.render import _ensure_full_x3d
    out = _ensure_full_x3d('<Shape><Box/></Shape>')
    assert out.lstrip().startswith("<?xml")
    assert "<X3D" in out and "<Scene>" in out and "<Box/>" in out
    # a full document is passed through untouched
    full = '<?xml version="1.0"?>\n<X3D profile="Immersive"><Scene/></X3D>'
    assert _ensure_full_x3d(full) == full


def test_xite_page_loads_scene():
    from tools.render import _xite_page
    html = _xite_page(320, 240)
    assert "x_ite" in html
    assert 'src="scene.x3d"' in html


# ---- render_image: actual headless X_ITE render (Playwright-gated) ----

def test_render_xite_smoke():
    pytest.importorskip("playwright")
    import asyncio
    from tools.render import _render_xite_async
    scene = (
        '<X3D profile="Immersive" version="4.1"><Scene>'
        '<Viewpoint position="0 0 6"/>'
        '<DirectionalLight direction="-0.3 -0.5 -1" intensity="1"/>'
        '<Shape><Appearance><Material diffuseColor="0.85 0.2 0.2"/></Appearance>'
        '<Box size="2 2 2"/></Shape></Scene></X3D>'
    )
    png = asyncio.run(_render_xite_async(scene, 320, 240, 6000))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"   # valid PNG signature
    assert len(png) > 500                     # not an empty frame


def test_render_xite_path_smoke(tmp_path):
    pytest.importorskip("playwright")
    import asyncio
    from tools.render import _render_xite_path_async
    f = tmp_path / "scene.x3d"
    f.write_text(
        '<X3D profile="Immersive" version="4.1"><Scene>'
        '<Viewpoint position="0 0 6"/>'
        '<DirectionalLight direction="-0.3 -0.5 -1" intensity="1"/>'
        '<Shape><Appearance><Material diffuseColor="0.2 0.6 0.9"/></Appearance>'
        '<Box size="2 2 2"/></Shape></Scene></X3D>'
    )
    png = asyncio.run(_render_xite_path_async(str(f), 320, 240, 6000))
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 500
    # the temp preview page is cleaned up
    assert not list(tmp_path.glob("._x3d_render_*.html"))
