"""Integration tests for MCP tools."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validation.validate import validate_xml


def test_workflow_create_scene():
    from tools.workflow import _serialize
    from x3d.x3d import X3D, Scene, head, meta, Shape, Box

    model = X3D(
        profile="Interchange", version="4.1",
        head=head(children=[meta(name="title", content="Test")]),
        Scene=Scene(children=[Shape(geometry=Box())]),
    )
    xml = _serialize(model, "xml")
    assert "<X3D" in xml
    assert "Interchange" in xml
    result = validate_xml(xml)
    assert result["valid"] is True


def test_workflow_create_geometry():
    from x3d.x3d import X3D, Scene, Shape, Appearance, Material, Box
    model = X3D(
        profile="Interchange", version="4.1",
        Scene=Scene(children=[
            Shape(
                appearance=Appearance(material=Material(diffuseColor=(1, 0, 0))),
                geometry=Box(size=(2, 2, 2)),
            )
        ]),
    )
    xml = model.XML()
    result = validate_xml(xml)
    assert result["valid"] is True
    assert "diffuseColor" in xml


def test_workflow_compose_scene():
    from x3d.x3d import (
        X3D, Scene, Shape, Appearance, Material, Box, Sphere,
        Transform, Viewpoint, DirectionalLight, Background,
    )
    model = X3D(
        profile="Interchange", version="4.1",
        Scene=Scene(children=[
            Background(skyColor=[(0.2, 0.2, 0.4)]),
            Viewpoint(position=(0, 2, 10), description="Main View"),
            DirectionalLight(direction=(0, -1, -1)),
            Transform(
                translation=(2, 0, 0),
                children=[Shape(
                    appearance=Appearance(material=Material(diffuseColor=(1, 0, 0))),
                    geometry=Box(),
                )],
            ),
            Shape(
                appearance=Appearance(material=Material(diffuseColor=(0, 0, 1))),
                geometry=Sphere(radius=1.5),
            ),
        ]),
    )
    xml = model.XML()
    result = validate_xml(xml)
    assert result["valid"] is True
    assert "Background" in xml
    assert "Viewpoint" in xml
    assert "DirectionalLight" in xml


def test_granular_scene_building():
    from x3d_utils.scene import SceneManager
    sm = SceneManager()

    shape_id = sm.create_node("Shape")
    app_id = sm.create_node("Appearance")
    mat_id = sm.create_node("Material", diffuseColor=(0, 1, 0))
    box_id = sm.create_node("Box")

    sm.add_child(app_id, mat_id)
    sm.add_child(shape_id, app_id)
    sm.add_child(shape_id, box_id)

    xml = sm.to_xml()
    result = validate_xml(xml)
    assert result["valid"] is True
    assert "Material" in xml
    assert "Box" in xml


def test_granular_def_use():
    from x3d_utils.scene import SceneManager
    sm = SceneManager()

    shape_id = sm.create_node("Shape")
    sm.def_node(shape_id, "MyShape")
    use_id = sm.use_node("MyShape")

    xml = sm.to_xml()
    assert "DEF='MyShape'" in xml
    assert "USE='MyShape'" in xml


def test_query_list_nodes():
    from x3d_utils.x3duom import get_x3duom
    uom = get_x3duom()
    components = uom.get_components()
    geo3d = components.get("Geometry3D", [])
    assert "Box" in geo3d
    assert "Sphere" in geo3d
    assert "Cylinder" in geo3d
    assert "Cone" in geo3d


def test_query_describe_node():
    from x3d_utils.x3duom import get_x3duom
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    box = nodes["Box"]
    assert box["component"] == "Geometry3D"
    assert box["containerField"] == "geometry"


def test_query_list_components():
    from x3d_utils.x3duom import get_x3duom
    uom = get_x3duom()
    components = uom.get_components()
    assert len(components) == 36


def test_query_list_profiles():
    from x3d_utils.x3duom import get_x3duom
    uom = get_x3duom()
    profiles = uom.get_profiles()
    assert "Interchange" in profiles
    assert "Full" in profiles


def test_convert_xml_to_json():
    from tools.convert import _parse_xml_to_model
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <Scene>
    <Shape>
      <Appearance>
        <Material diffuseColor="1 0 0"/>
      </Appearance>
      <Box size="2 2 2"/>
    </Shape>
  </Scene>
</X3D>"""
    model = _parse_xml_to_model(xml)
    json_out = model.JSON()
    assert "X3D" in json_out
    assert "Material" in json_out


def test_convert_xml_to_vrml():
    from tools.convert import _parse_xml_to_model
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <Scene>
    <Shape>
      <Appearance>
        <Material diffuseColor="0 1 0"/>
      </Appearance>
      <Sphere radius="2.0"/>
    </Shape>
  </Scene>
</X3D>"""
    model = _parse_xml_to_model(xml)
    vrml = model.VRML()
    assert "#VRML" in vrml
    assert "Sphere" in vrml
