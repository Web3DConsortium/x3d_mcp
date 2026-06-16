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


# ---- containerField correctness (X3DUOM-driven) ----

def test_containerfield_texture_in_physicalmaterial():
    # ImageTexture's default containerField 'texture' does not fit PhysicalMaterial
    xml = _wrap("<Shape><Appearance><PhysicalMaterial>"
                "<ImageTexture url='&quot;t.png&quot;'/>"
                "</PhysicalMaterial></Appearance><Box/></Shape>")
    report = validate_semantic(xml)
    assert "containerfield-unknown" in report
    assert "baseTexture" in report  # suggests a valid slot


def test_containerfield_explicit_texture_ok():
    xml = _wrap("<Shape><Appearance><PhysicalMaterial>"
                "<ImageTexture containerField='baseTexture' url='&quot;t.png&quot;'/>"
                "</PhysicalMaterial></Appearance><Box/></Shape>")
    report = validate_semantic(xml)
    assert "containerfield" not in report


def test_containerfield_texture_in_appearance_ok():
    # Appearance HAS a 'texture' field, so the default placement is correct
    xml = _wrap("<Shape><Appearance>"
                "<ImageTexture url='&quot;t.png&quot;'/>"
                "</Appearance><Box/></Shape>")
    report = validate_semantic(xml)
    assert "containerfield" not in report


def test_containerfield_hanim_joint_default_in_humanoid():
    xml = _wrap("<HAnimHumanoid name='h'><HAnimJoint name='root'/></HAnimHumanoid>")
    report = validate_semantic(xml)
    assert "containerfield" in report
    assert "joints" in report or "skeleton" in report


def test_containerfield_clean_scene_no_flag():
    xml = _wrap("<Transform><Shape><Appearance><Material/></Appearance>"
                "<Box/></Shape></Transform>")
    report = validate_semantic(xml)
    assert "containerfield" not in report


# ---- USE-before-DEF ordering ----

def test_use_before_def_flagged():
    xml = _wrap('<Group><Shape USE="S"/></Group>'
                '<Shape DEF="S"><Appearance><Material/></Appearance><Box/></Shape>')
    report = validate_semantic(xml)
    assert "use-before-def" in report


def test_def_before_use_ok():
    xml = _wrap('<Shape DEF="S"><Appearance><Material/></Appearance><Box/></Shape>'
                '<Group><Shape USE="S"/></Group>')
    report = validate_semantic(xml)
    assert "use-before-def" not in report


# ---- interpolator key / keyValue length ----

def test_orientation_interpolator_wrong_arity():
    xml = _wrap('<OrientationInterpolator key="0 0.5 1" keyValue="0 1 0 0  0 1 0 1.5"/>')
    report = validate_semantic(xml)
    assert "interpolator-key-length" in report  # 3 keys need 12 floats, got 8


def test_orientation_interpolator_ok():
    xml = _wrap('<OrientationInterpolator key="0 0.5 1" '
                'keyValue="0 1 0 0  0 1 0 1.5  0 1 0 3"/>')
    report = validate_semantic(xml)
    assert "interpolator-key-length" not in report


def test_coordinate_interpolator_variable_ok():
    # 2 keys, 2 coords each -> 12 floats, a multiple of 3 per key (6)
    xml = _wrap('<CoordinateInterpolator key="0 1" '
                'keyValue="0 0 0 1 1 1  0 0 0 2 2 2"/>')
    report = validate_semantic(xml)
    assert "interpolator-key-length" not in report


def test_scalar_interpolator_not_divisible():
    xml = _wrap('<ScalarInterpolator key="0 0.5 1" keyValue="0 1"/>')
    report = validate_semantic(xml)
    assert "interpolator-key-length" in report
