"""Tests for containerField auto-fix (returns a corrected X3D document)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validation.autofix import autofix_containerfields
from validation.semantic import validate_semantic


def _wrap(body: str) -> str:
    return ('<?xml version="1.0"?><X3D profile="Full" version="4.1">'
            f'<Scene>{body}</Scene></X3D>')


def test_texture_in_physicalmaterial_fixed_to_basetexture():
    src = _wrap("<Shape><Appearance><PhysicalMaterial>"
                "<ImageTexture url='&quot;t.png&quot;'/>"
                "</PhysicalMaterial></Appearance><Box/></Shape>")
    res = autofix_containerfields(src)
    chg = res["changes"]
    assert len(chg) == 1
    assert chg[0]["node"] == "ImageTexture" and chg[0]["to"] == "baseTexture"
    assert chg[0]["ambiguous"] is True
    assert "baseTexture" in res["fixed"]
    # the fixed document re-validates with no containerField errors
    assert "containerfield" not in validate_semantic(res["fixed"])


def test_hanim_skeleton_root_fixed_to_skeleton():
    src = _wrap("<HAnimHumanoid name='h'>"
                "<HAnimJoint DEF='root' name='root'/></HAnimHumanoid>")
    res = autofix_containerfields(src)
    assert res["changes"][0]["to"] == "skeleton"
    assert "containerfield" not in validate_semantic(res["fixed"])


def test_pipe_separated_acceptance_not_flagged():
    # HAnimJoint.children accepts 'HAnimJoint|HAnimSegment' -> a Segment is valid here
    src = _wrap("<HAnimHumanoid name='h'><HAnimJoint DEF='r' containerField='skeleton' "
                "name='r'><HAnimSegment name='s'/></HAnimJoint></HAnimHumanoid>")
    res = autofix_containerfields(src)
    assert res["changes"] == []
    assert res["unfixable"] == []


def test_explicit_wrong_containerfield_corrected():
    src = _wrap("<Shape><Appearance><PhysicalMaterial>"
                "<ImageTexture containerField='diffuseTexture' url='&quot;t.png&quot;'/>"
                "</PhysicalMaterial></Appearance><Box/></Shape>")
    res = autofix_containerfields(src)
    assert res["changes"][0]["from"] == "diffuseTexture"
    assert res["changes"][0]["to"] == "baseTexture"


def test_clean_document_unchanged():
    src = _wrap("<Transform><Shape><Appearance><Material/></Appearance>"
                "<Box/></Shape></Transform>")
    res = autofix_containerfields(src)
    assert res["changes"] == []
    assert res["unfixable"] == []


def test_unfixable_when_no_field_accepts():
    # A Box has no field that accepts a Material -- a real misplacement
    src = _wrap("<Shape><Box><Material/></Box></Shape>")
    res = autofix_containerfields(src)
    assert any(u["node"] == "Material" for u in res["unfixable"])


def test_parse_error():
    res = autofix_containerfields("<broken")
    assert "error" in res
