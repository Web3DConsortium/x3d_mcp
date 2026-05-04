"""Tests for the X3DUOM parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from x3d_utils.x3duom import get_x3duom, X3DUOM


def test_loads_x3duom():
    uom = get_x3duom()
    assert isinstance(uom, X3DUOM)


def test_concrete_nodes_count():
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    assert len(nodes) == 265


def test_box_node():
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    box = nodes["Box"]
    assert box["component"] == "Geometry3D"
    assert box["baseType"] == "X3DGeometryNode"
    assert box["containerField"] == "geometry"
    field_names = {f["name"] for f in box["fields"]}
    assert "size" in field_names
    assert "solid" in field_names


def test_material_node():
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    mat = nodes["Material"]
    assert mat["component"] == "Shape"
    field_names = {f["name"] for f in mat["fields"]}
    assert "diffuseColor" in field_names
    assert "transparency" in field_names
    assert "shininess" in field_names


def test_transform_node():
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    xform = nodes["Transform"]
    assert xform["component"] == "Grouping"
    field_names = {f["name"] for f in xform["fields"]}
    assert "translation" in field_names
    assert "rotation" in field_names
    assert "scale" in field_names
    assert "children" in field_names


def test_get_node_fields():
    uom = get_x3duom()
    fields = uom.get_node_fields("Box")
    assert len(fields) > 0
    size_field = next(f for f in fields if f["name"] == "size")
    assert size_field["type"] == "SFVec3f"
    assert size_field["default"] == "2 2 2"


def test_get_node_fields_unknown():
    uom = get_x3duom()
    fields = uom.get_node_fields("FakeNode")
    assert fields == []


def test_components():
    uom = get_x3duom()
    components = uom.get_components()
    assert len(components) == 36
    assert "Geometry3D" in components
    assert "Shape" in components
    assert "Grouping" in components
    assert "Box" in components["Geometry3D"]
    assert "Sphere" in components["Geometry3D"]


def test_profiles():
    uom = get_x3duom()
    profiles = uom.get_profiles()
    assert "Core" in profiles
    assert "Interchange" in profiles
    assert "Immersive" in profiles
    assert "Full" in profiles


def test_field_types():
    uom = get_x3duom()
    types = uom.get_field_types()
    assert len(types) == 42
    assert "SFBool" in types
    assert types["SFBool"]["isArray"] is False
    assert types["MFFloat"]["isArray"] is True
    assert types["SFVec3f"]["tupleSize"] == 3
    assert types["SFColor"]["tupleSize"] == 3


def test_abstract_types():
    uom = get_x3duom()
    abstract = uom.get_abstract_types()
    assert len(abstract) > 0
    assert "X3DNode" in abstract
    assert "X3DGeometryNode" in abstract
    assert "X3DGroupingNode" in abstract


def test_container_field():
    uom = get_x3duom()
    assert uom.get_container_field("Box") == "geometry"
    assert uom.get_container_field("Material") == "material"
    assert uom.get_container_field("Shape") == "children"
    assert uom.get_container_field("Transform") == "children"
    assert uom.get_container_field("Appearance") == "appearance"
    assert uom.get_container_field("FakeNode") is None


def test_singleton():
    uom1 = get_x3duom()
    uom2 = get_x3duom()
    assert uom1 is uom2
