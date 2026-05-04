"""Tests for example scenes -- validate all .x3d files pass XSD (Issue #6)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validation.validate import validate_xml

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples" / "scenes"


def _get_scene_files():
    return sorted(EXAMPLES_DIR.glob("*.x3d"))


def test_example_scenes_exist():
    scenes = _get_scene_files()
    assert len(scenes) >= 3, f"Expected at least 3 example scenes, found {len(scenes)}"


def test_red_sphere_valid():
    path = EXAMPLES_DIR / "red_sphere.x3d"
    result = validate_xml(path.read_text())
    assert result["valid"], f"red_sphere.x3d: {result['errors']}"


def test_table_scene_valid():
    path = EXAMPLES_DIR / "table_scene.x3d"
    result = validate_xml(path.read_text())
    assert result["valid"], f"table_scene.x3d: {result['errors']}"


def test_doha_scene_valid():
    path = EXAMPLES_DIR / "doha_qatar.x3d"
    result = validate_xml(path.read_text())
    assert result["valid"], f"doha_qatar.x3d: {result['errors']}"


def test_all_example_scenes_valid():
    scenes = _get_scene_files()
    for scene_path in scenes:
        xml = scene_path.read_text()
        result = validate_xml(xml)
        assert result["valid"], f"{scene_path.name}: {result['errors']}"
