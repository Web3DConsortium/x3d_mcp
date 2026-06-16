"""Tests for the shared X3D source resolver (inline content OR file path)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from x3d_utils.source import load_x3d_source


def test_inline_content():
    assert load_x3d_source(content="<X3D/>") == "<X3D/>"


def test_path(tmp_path):
    f = tmp_path / "scene.x3d"
    f.write_text("<X3D>file</X3D>", encoding="utf-8")
    assert load_x3d_source(path=str(f)) == "<X3D>file</X3D>"


def test_neither_raises():
    with pytest.raises(ValueError, match="either"):
        load_x3d_source()


def test_both_raises():
    with pytest.raises(ValueError, match="not both"):
        load_x3d_source(content="<X3D/>", path="/tmp/x.x3d")


def test_missing_file_raises(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        load_x3d_source(path=str(tmp_path / "nope.x3d"))


def test_validate_x3d_accepts_path(tmp_path):
    """The validate_semantic pipeline should run on a file loaded by path."""
    from validation.semantic import validate_semantic
    f = tmp_path / "bad.x3d"
    f.write_text(
        '<?xml version="1.0"?><X3D profile="Full" version="4.1"><Scene>'
        '<Shape><Appearance><PhysicalMaterial>'
        '<ImageTexture url=\'"t.png"\'/></PhysicalMaterial></Appearance><Box/></Shape>'
        '</Scene></X3D>', encoding="utf-8")
    report = validate_semantic(load_x3d_source(path=str(f)))
    assert "containerfield-unknown" in report
