"""Tests for HTTP-transport guards: per-session scene state and
file-path input rejection."""

import pytest

from tools.granular import _scene, _scene_for
from tools.scene_ops import _modify_node, _parse_x3d_source


INLINE_SCENE = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile='Interchange' version='4.1'>
  <Scene>
    <Transform DEF='Target'/>
  </Scene>
</X3D>"""


class _FakeCtx:
    """Stands in for fastmcp Context: exposes a .session attribute."""

    def __init__(self, session):
        self.session = session


class _RaisingCtx:
    """Mimics Context outside a live request: .session raises."""

    @property
    def session(self):
        raise ValueError("Context is not available outside of a request")


class _Session:
    """Weakref-able stand-in for an MCP ServerSession."""


def test_scene_for_none_falls_back_to_module_scene():
    assert _scene_for(None) is _scene


def test_scene_for_no_request_context_falls_back():
    assert _scene_for(_RaisingCtx()) is _scene


def test_scene_for_isolates_sessions():
    a, b = _Session(), _Session()
    scene_a = _scene_for(_FakeCtx(a))
    scene_b = _scene_for(_FakeCtx(b))
    assert scene_a is not scene_b
    assert scene_a is not _scene

    node_id = scene_a.create_node("Transform")
    assert node_id in scene_a._nodes
    assert node_id not in scene_b._nodes


def test_scene_for_same_session_is_stable():
    s = _Session()
    assert _scene_for(_FakeCtx(s)) is _scene_for(_FakeCtx(s))


def test_file_path_rejected_over_http(monkeypatch, tmp_path):
    scene_file = tmp_path / "scene.x3d"
    scene_file.write_text(INLINE_SCENE)

    monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
    with pytest.raises(ValueError, match="disabled over the HTTP transport"):
        _parse_x3d_source(str(scene_file))


def test_file_path_allowed_under_stdio(monkeypatch, tmp_path):
    scene_file = tmp_path / "scene.x3d"
    scene_file.write_text(INLINE_SCENE)

    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    tree = _parse_x3d_source(str(scene_file))
    assert tree is not None


def test_inline_xml_still_works_over_http(monkeypatch):
    monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
    result = _modify_node(INLINE_SCENE, "Target", {"translation": "1 2 3"})
    assert "translation" in result
    assert "1 2 3" in result
