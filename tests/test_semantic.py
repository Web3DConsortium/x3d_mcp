"""Tests for the semantic validation pipeline.

Mirrors the 19-test inventory in
https://github.com/niknarra/x3d-mcp/blob/main/tests/test_semantic_check.py
(Nikhil Narra, Nicholas Polys -- Virginia Tech / Web3D Consortium).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validation.semantic import validate_semantic


def _wrap(scene_body: str, profile: str = "Immersive") -> str:
    """Wrap scene body XML in an X3D 4.1 document."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<X3D profile="{profile}" version="4.1">\n'
        f'  <Scene>{scene_body}</Scene>\n'
        f'</X3D>'
    )


# ---- Shape completeness ----

def test_shape_no_geometry():
    xml = _wrap("<Shape><Appearance><Material/></Appearance></Shape>")
    report = validate_semantic(xml)
    assert "shape-no-geometry" in report
    assert "Warning" in report or "warning" in report


def test_shape_no_appearance():
    xml = _wrap("<Shape><Box/></Shape>")
    report = validate_semantic(xml)
    assert "shape-no-appearance" in report


def test_complete_shape_no_warning():
    xml = _wrap("<Shape><Appearance><Material/></Appearance><Box/></Shape>")
    report = validate_semantic(xml)
    assert "shape-no-geometry" not in report
    assert "shape-no-appearance" not in report


# ---- Empty grouping nodes ----

def test_empty_transform():
    xml = _wrap("<Transform/>")
    report = validate_semantic(xml)
    assert "empty-group" in report


def test_transform_with_children_ok():
    xml = _wrap("<Transform><Shape><Box/></Shape></Transform>")
    report = validate_semantic(xml)
    assert "empty-group" not in report


# ---- DEF/USE consistency ----

def test_use_references_undefined_def():
    xml = _wrap('<Shape USE="GhostShape"/>')
    report = validate_semantic(xml)
    assert "use-undefined-def" in report
    assert "GhostShape" in report


def test_unused_def_info():
    xml = _wrap('<Shape DEF="Lonely"><Box/></Shape>')
    report = validate_semantic(xml)
    assert "unused-def" in report
    assert "Lonely" in report


def test_consistent_def_use():
    xml = _wrap(
        '<Shape DEF="Master"><Box/></Shape>'
        '<Transform><Shape USE="Master"/></Transform>'
    )
    report = validate_semantic(xml)
    assert "use-undefined-def" not in report
    assert "unused-def" not in report


# ---- Duplicate DEFs ----

def test_duplicate_def_names():
    xml = _wrap(
        '<Shape DEF="Twin"><Box/></Shape>'
        '<Shape DEF="Twin"><Sphere/></Shape>'
    )
    report = validate_semantic(xml)
    assert "duplicate-def" in report
    assert "Twin" in report


def test_unique_defs_ok():
    xml = _wrap(
        '<Shape DEF="A"><Box/></Shape>'
        '<Shape DEF="B"><Sphere/></Shape>'
    )
    report = validate_semantic(xml)
    assert "duplicate-def" not in report


# ---- ROUTE validity ----

def test_route_nonexistent_from_node():
    xml = _wrap(
        '<TimeSensor DEF="Clock" cycleInterval="2"/>'
        '<Transform DEF="Spinner"/>'
        '<ROUTE fromNode="GhostNode" fromField="fraction_changed" '
        'toNode="Spinner" toField="set_rotation"/>'
    )
    report = validate_semantic(xml)
    assert "route-missing-from-node" in report


def test_route_nonexistent_to_node():
    xml = _wrap(
        '<TimeSensor DEF="Clock" cycleInterval="2"/>'
        '<ROUTE fromNode="Clock" fromField="cycleTime" '
        'toNode="GhostNode" toField="set_fraction"/>'
    )
    report = validate_semantic(xml)
    assert "route-missing-to-node" in report


def test_route_invalid_field():
    xml = _wrap(
        '<TimeSensor DEF="Clock" cycleInterval="2"/>'
        '<Transform DEF="Spinner"><Shape><Box/></Shape></Transform>'
        '<ROUTE fromNode="Clock" fromField="totally_made_up_field" '
        'toNode="Spinner" toField="set_translation"/>'
    )
    report = validate_semantic(xml)
    assert "route-invalid-from-field" in report


def test_valid_route_no_error():
    xml = _wrap(
        '<TimeSensor DEF="Clock" cycleInterval="2" loop="true"/>'
        '<Transform DEF="Spinner"><Shape><Box/></Shape></Transform>'
        '<ROUTE fromNode="Clock" fromField="cycleTime" '
        'toNode="Spinner" toField="rotation"/>'
    )
    report = validate_semantic(xml)
    assert "route-missing-from-node" not in report
    assert "route-missing-to-node" not in report
    assert "route-invalid-from-field" not in report
    assert "route-invalid-to-field" not in report


# ---- Missing viewpoint ----

def test_no_viewpoint_info():
    xml = _wrap("<Shape><Box/></Shape>")
    report = validate_semantic(xml)
    assert "no-viewpoint" in report


def test_with_viewpoint_ok():
    xml = _wrap(
        '<Viewpoint position="0 0 10"/>'
        '<Shape><Appearance><Material/></Appearance><Box/></Shape>'
    )
    report = validate_semantic(xml)
    assert "no-viewpoint" not in report


# ---- Overall report shape ----

def test_clean_scene_structure():
    xml = _wrap(
        '<Viewpoint position="0 0 10"/>'
        '<Shape><Appearance><Material/></Appearance><Box/></Shape>'
    )
    report = validate_semantic(xml)
    assert "All Clear" in report


def test_multiple_issues_all_reported():
    xml = _wrap(
        '<Shape DEF="Twin"><Box/></Shape>'        # no appearance -> info
        '<Shape DEF="Twin"><Sphere/></Shape>'     # duplicate DEF -> error
        '<Shape><Appearance><Material/></Appearance></Shape>'  # no geometry -> warning
        '<Transform/>'                             # empty group -> warning
        '<Shape USE="GhostShape"/>'                # USE without DEF -> error
    )
    report = validate_semantic(xml)
    assert "duplicate-def" in report
    assert "shape-no-geometry" in report
    assert "empty-group" in report
    assert "use-undefined-def" in report
    assert "no-viewpoint" in report
    assert "## Errors" in report
    assert "## Warnings" in report
    assert "## Info" in report


def test_invalid_xml_source():
    report = validate_semantic("<broken")
    assert "Parse Error" in report


# ---- ROUTEs into dynamic interfaces (Script <field> + ProtoInstance) ----
# A Script's user-declared fields and a ProtoInstance's interface are not in
# X3DUOM, so the route-validity check must read them from the scene -- otherwise
# every valid ROUTE into a Script/proto field is false-flagged route-invalid.

def test_route_to_script_declared_field_is_valid():
    xml = _wrap(
        '<TimeSensor DEF="T" cycleInterval="2" loop="true"/>'
        '<Script DEF="S" directOutput="true">'
        '<field name="arrived" type="SFTime" accessType="inputOnly"/></Script>'
        '<ROUTE fromNode="T" fromField="cycleTime" toNode="S" toField="arrived"/>')
    report = validate_semantic(xml)
    assert "route-invalid-to-field" not in report   # 'arrived' is a declared field


def test_route_to_protoinstance_interface_field_is_valid():
    xml = _wrap(
        '<ProtoDeclare name="Mover"><ProtoInterface>'
        '<field name="set_time" type="SFTime" accessType="inputOnly"/>'
        '</ProtoInterface><ProtoBody><Transform/></ProtoBody></ProtoDeclare>'
        '<TimeSensor DEF="T" cycleInterval="2"/>'
        '<Mover DEF="M"/>'
        '<ROUTE fromNode="T" fromField="cycleTime" toNode="M" toField="set_time"/>')
    report = validate_semantic(xml)
    assert "route-invalid-to-field" not in report   # 'set_time' is in the interface


def test_route_to_truly_missing_script_field_still_flagged():
    xml = _wrap(
        '<TimeSensor DEF="T" cycleInterval="2"/>'
        '<Script DEF="S"><field name="arrived" type="SFTime" accessType="inputOnly"/></Script>'
        '<ROUTE fromNode="T" fromField="cycleTime" toNode="S" toField="nonexistent"/>')
    report = validate_semantic(xml)
    assert "route-invalid-to-field" in report        # a real typo is still caught
