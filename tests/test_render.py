"""Tests for the X3DOM rendering tool.

Mirrors the 7 X3DOM tests in
https://github.com/niknarra/x3d-mcp/blob/main/tests/test_generation.py
(Nikhil Narra, Nicholas Polys -- Virginia Tech / Web3D Consortium).
"""

import sys
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
