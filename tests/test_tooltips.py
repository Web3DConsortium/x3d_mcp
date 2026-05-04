"""Tests for X3D tooltips parser and cross-reference (Issue #5)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from x3d_utils.tooltips import get_tooltips, X3DTooltips, _split_tooltip
from x3d_utils.x3duom import get_x3duom


class TestTooltipParsing:
    def test_loads_tooltips(self):
        tips = get_tooltips()
        assert isinstance(tips, X3DTooltips)

    def test_has_nodes(self):
        tips = get_tooltips()
        nodes = tips.get_nodes()
        assert len(nodes) > 100

    def test_box_node_exists(self):
        tips = get_tooltips()
        box = tips.get_node_tooltip("Box")
        assert box is not None
        assert "fields" in box

    def test_box_has_size_field(self):
        tips = get_tooltips()
        size = tips.get_field_tooltip("Box", "size")
        assert size is not None
        assert size["description"]

    def test_material_node_exists(self):
        tips = get_tooltips()
        mat = tips.get_node_tooltip("Material")
        assert mat is not None

    def test_transform_node_exists(self):
        tips = get_tooltips()
        xform = tips.get_node_tooltip("Transform")
        assert xform is not None
        fields = xform["fields"]
        assert "translation" in fields
        assert "rotation" in fields
        assert "scale" in fields

    def test_appearance_has_material_field(self):
        tips = get_tooltips()
        mat = tips.get_field_tooltip("Appearance", "material")
        assert mat is not None
        assert mat["description"]

    def test_unknown_node_returns_none(self):
        tips = get_tooltips()
        assert tips.get_node_tooltip("FakeNode999") is None

    def test_unknown_field_returns_none(self):
        tips = get_tooltips()
        assert tips.get_field_tooltip("Box", "fakeField999") is None

    def test_get_node_names(self):
        tips = get_tooltips()
        names = tips.get_node_names()
        assert "Box" in names
        assert "Material" in names
        assert "Transform" in names

    def test_singleton(self):
        t1 = get_tooltips()
        t2 = get_tooltips()
        assert t1 is t2


class TestSplitTooltip:
    def test_extracts_description(self):
        result = _split_tooltip("[X3DGeometryNode] Box is a geometry node.")
        assert result["baseType"] == "X3DGeometryNode"
        assert "Box is a geometry node" in result["description"]

    def test_extracts_hints(self):
        raw = "Some description.\nHint: use DEF/USE for efficiency.\nHint: see spec."
        result = _split_tooltip(raw)
        assert len(result["hints"]) == 2
        assert "DEF/USE" in result["hints"][0]

    def test_extracts_warnings(self):
        raw = "Description.\nWarning: do not use with scripts."
        result = _split_tooltip(raw)
        assert len(result["warnings"]) == 1
        assert "scripts" in result["warnings"][0]

    def test_extracts_urls(self):
        raw = "Description.\nHint: see https://www.web3d.org/spec for details."
        result = _split_tooltip(raw)
        assert len(result["specUrls"]) == 1
        assert "web3d.org" in result["specUrls"][0]

    def test_empty_tooltip(self):
        result = _split_tooltip("")
        assert result["description"] == ""
        assert result["hints"] == []
        assert result["warnings"] == []


class TestEnrichedNode:
    def test_enriched_box(self):
        uom = get_x3duom()
        box = uom.get_enriched_node("Box")
        assert box is not None
        assert box["component"] == "Geometry3D"
        assert isinstance(box.get("tooltip"), str)
        assert isinstance(box.get("hints"), list)

    def test_enriched_box_fields_have_tooltips(self):
        uom = get_x3duom()
        box = uom.get_enriched_node("Box")
        size_field = next((f for f in box["fields"] if f["name"] == "size"), None)
        assert size_field is not None
        assert "tooltip" in size_field

    def test_enriched_material(self):
        uom = get_x3duom()
        mat = uom.get_enriched_node("Material")
        assert mat is not None
        dc = next((f for f in mat["fields"] if f["name"] == "diffuseColor"), None)
        assert dc is not None
        assert "tooltip" in dc

    def test_enriched_unknown_returns_none(self):
        uom = get_x3duom()
        assert uom.get_enriched_node("FakeNode999") is None

    def test_enriched_preserves_uom_data(self):
        uom = get_x3duom()
        box = uom.get_enriched_node("Box")
        assert box["containerField"] == "geometry"
        assert box["baseType"] == "X3DGeometryNode"
        size_field = next(f for f in box["fields"] if f["name"] == "size")
        assert size_field["type"] == "SFVec3f"
        assert size_field["default"] == "2 2 2"


class TestCoverageReport:
    def test_report_structure(self):
        uom = get_x3duom()
        report = uom.get_coverage_report()
        assert "uom_node_count" in report
        assert "tips_node_count" in report
        assert "common_nodes" in report
        assert "uom_only_nodes" in report
        assert "tips_only_nodes" in report
        assert "field_drift" in report

    def test_uom_has_265_nodes(self):
        uom = get_x3duom()
        report = uom.get_coverage_report()
        assert report["uom_node_count"] == 265

    def test_common_nodes_exist(self):
        uom = get_x3duom()
        report = uom.get_coverage_report()
        assert report["common_nodes"] > 100

    def test_report_lists_are_sorted(self):
        uom = get_x3duom()
        report = uom.get_coverage_report()
        assert report["uom_only_nodes"] == sorted(report["uom_only_nodes"])
        assert report["tips_only_nodes"] == sorted(report["tips_only_nodes"])
