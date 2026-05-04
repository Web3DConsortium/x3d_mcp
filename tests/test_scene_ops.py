"""Tests for X3D scene manipulation: modify, remove, and move nodes.

Mirrors the 26-test inventory in
https://github.com/niknarra/x3d-mcp/blob/main/tests/test_scene_manipulation.py
(Nikhil Narra, Nicholas Polys -- Virginia Tech / Web3D Consortium).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tools.scene_ops import _modify_node, _remove_node, _move_node
from validation.validate import validate_xml


SAMPLE_SCENE = '''<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <Scene>
    <Viewpoint DEF="MainView" description="Default View" position="0 0 10"/>
    <DirectionalLight DEF="Sun" direction="0 -1 -1" intensity="0.8"/>
    <Transform DEF="RedGroup" translation="2 0 0">
      <Shape DEF="RedShape">
        <Appearance>
          <Material DEF="RedMat" diffuseColor="1 0 0"/>
        </Appearance>
        <Sphere radius="1.5"/>
      </Shape>
    </Transform>
    <Transform DEF="BlueGroup" translation="-2 0 0">
      <Shape DEF="BlueShape">
        <Appearance>
          <Material DEF="BlueMat" diffuseColor="0 0 1" transparency="0.3"/>
        </Appearance>
        <Box size="2 2 2"/>
      </Shape>
    </Transform>
  </Scene>
</X3D>'''


# ---- modify_node ----

def test_modify_single_attribute():
    result = _modify_node(SAMPLE_SCENE, "RedMat", {"diffuseColor": "0 1 0"})
    assert 'diffuseColor="0 1 0"' in result
    assert "1 0 0" not in result.split("RedMat")[1].split("/>")[0]


def test_modify_multiple_fields():
    result = _modify_node(SAMPLE_SCENE, "RedGroup", {
        "translation": "5 5 5",
        "rotation": "0 1 0 1.57",
    })
    assert 'translation="5 5 5"' in result
    assert 'rotation="0 1 0 1.57"' in result


def test_modify_preserves_other_attributes():
    result = _modify_node(SAMPLE_SCENE, "BlueMat", {"diffuseColor": "0 1 0"})
    assert 'diffuseColor="0 1 0"' in result
    assert 'transparency="0.3"' in result


def test_modify_nonexistent_def():
    result = _modify_node(SAMPLE_SCENE, "DoesNotExist", {"foo": "bar"})
    assert "DoesNotExist" in result
    assert "Available DEF names" in result


def test_modify_no_def():
    result = _modify_node(SAMPLE_SCENE, "", {"foo": "bar"})
    assert "def_name is required" in result.lower()


def test_modify_no_changes():
    result = _modify_node(SAMPLE_SCENE, "RedMat", {})
    assert "No field_changes" in result


def test_modified_scene_validates():
    result = _modify_node(SAMPLE_SCENE, "RedMat", {"diffuseColor": "0 1 0"})
    assert validate_xml(result)["valid"] is True


def test_modify_adds_new_attribute():
    result = _modify_node(SAMPLE_SCENE, "RedMat", {"shininess": "0.8"})
    assert 'shininess="0.8"' in result


# ---- remove_node ----

def test_remove_by_def():
    result = _remove_node(SAMPLE_SCENE, def_name="RedGroup")
    assert "RedGroup" not in result
    assert "BlueGroup" in result


def test_remove_by_type_and_index():
    result = _remove_node(SAMPLE_SCENE, node_type="Transform", index=1)
    assert "BlueGroup" not in result
    assert "RedGroup" in result


def test_remove_preserves_siblings():
    result = _remove_node(SAMPLE_SCENE, def_name="Sun")
    assert "Sun" not in result
    assert "MainView" in result
    assert "RedGroup" in result
    assert "BlueGroup" in result


def test_remove_nonexistent_def():
    result = _remove_node(SAMPLE_SCENE, def_name="FakeNode")
    assert "FakeNode" in result
    assert "Available DEF names" in result


def test_remove_nonexistent_type():
    result = _remove_node(SAMPLE_SCENE, node_type="IndexedFaceSet")
    assert "IndexedFaceSet" in result


def test_remove_type_index_out_of_range():
    result = _remove_node(SAMPLE_SCENE, node_type="Transform", index=99)
    assert "out of range" in result.lower()


def test_remove_no_identifiers():
    result = _remove_node(SAMPLE_SCENE)
    assert "def_name" in result.lower() or "node_type" in result.lower()


def test_removed_scene_validates():
    result = _remove_node(SAMPLE_SCENE, def_name="RedGroup")
    assert validate_xml(result)["valid"] is True


def test_remove_leaf_node():
    result = _remove_node(SAMPLE_SCENE, def_name="RedMat")
    assert "RedMat" not in result
    assert "RedGroup" in result


# ---- move_node ----

def test_move_to_new_parent():
    result = _move_node(SAMPLE_SCENE, "RedShape", new_parent_def="BlueGroup")
    assert "RedShape" in result
    assert "BlueGroup" in result


def test_move_to_scene_root():
    result = _move_node(SAMPLE_SCENE, "RedShape", new_parent_def="")
    assert "RedShape" in result


def test_move_nonexistent_source():
    result = _move_node(SAMPLE_SCENE, "FakeNode", new_parent_def="BlueGroup")
    assert "FakeNode" in result


def test_move_nonexistent_target():
    result = _move_node(SAMPLE_SCENE, "RedShape", new_parent_def="FakeParent")
    assert "FakeParent" in result


def test_move_to_self():
    result = _move_node(SAMPLE_SCENE, "RedGroup", new_parent_def="RedGroup")
    assert "Cannot move" in result or "itself" in result.lower()


def test_move_to_descendant():
    result = _move_node(SAMPLE_SCENE, "RedGroup", new_parent_def="RedMat")
    assert "cycle" in result.lower() or "descendant" in result.lower()


def test_move_already_at_parent():
    result = _move_node(SAMPLE_SCENE, "RedShape", new_parent_def="RedGroup")
    assert "already" in result.lower()


def test_moved_scene_validates():
    result = _move_node(SAMPLE_SCENE, "Sun", new_parent_def="RedGroup")
    assert validate_xml(result)["valid"] is True


def test_move_no_def():
    result = _move_node(SAMPLE_SCENE, "")
    assert "def_name is required" in result.lower()
