"""Tests for the validation pipeline."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from validation.validate import validate_xml, validate_json


def test_valid_minimal_scene():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <Scene>
    <Shape>
      <Appearance>
        <Material/>
      </Appearance>
      <Box/>
    </Shape>
  </Scene>
</X3D>"""
    result = validate_xml(xml)
    assert result["valid"] is True
    assert result["errors"] == []


def test_valid_scene_with_xsi():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1"
     xmlns:xsd="https://www.w3.org/2001/XMLSchema-instance"
     xsd:noNamespaceSchemaLocation="https://www.web3d.org/specifications/x3d-4.0.xsd">
  <Scene>
    <Shape>
      <Box/>
    </Shape>
  </Scene>
</X3D>"""
    result = validate_xml(xml)
    assert result["valid"] is True


def test_invalid_unknown_node():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile="Interchange" version="4.1">
  <Scene>
    <FakeNode/>
  </Scene>
</X3D>"""
    result = validate_xml(xml)
    assert result["valid"] is False
    assert any("FakeNode" in e for e in result["errors"])


def test_invalid_malformed_xml():
    result = validate_xml("<broken")
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_invalid_missing_profile():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<X3D version="4.1">
  <Scene/>
</X3D>"""
    result = validate_xml(xml)
    # XSD requires profile attribute
    assert result["valid"] is False


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _minimal_valid_json() -> str:
    """Canonical-shape minimal X3D JSON: encoding + Scene.-children populated.

    Note: `-geometry` and `-appearance` are SFNode containers (single object),
    not arrays. Web3D's HelloWorld.json shows the canonical shape.
    """
    return json.dumps({
        "X3D": {
            "encoding": "UTF-8",
            "@profile": "Interchange",
            "@version": "4.0",
            "Scene": {"-children": [{"Shape": {"-geometry": {"Box": {}}}}]},
        }
    })


def test_valid_json():
    result = validate_json(_minimal_valid_json())
    assert result["valid"] is True
    assert result["errors"] == []


def test_valid_canonical_helloworld():
    helloworld = (FIXTURES / "HelloWorld.json").read_text()
    result = validate_json(helloworld)
    assert result["valid"] is True, result["errors"][:5]


def test_invalid_json_parse():
    result = validate_json("{broken")
    assert result["valid"] is False
    assert "parse error" in result["errors"][0].lower()


def test_invalid_json_missing_x3d():
    result = validate_json('{"Scene": {}}')
    assert result["valid"] is False
    assert any("X3D" in e for e in result["errors"])


def test_invalid_json_missing_fields():
    result = validate_json('{"X3D": {}}')
    assert result["valid"] is False
    joined = " ".join(result["errors"])
    assert "@version" in joined
    assert "@profile" in joined
    assert "Scene" in joined
    assert "encoding" in joined


def test_invalid_json_misspelled_head():
    """Misspelled `head` -- John Carlson's example. Surface check missed this; schema catches it."""
    bad = json.dumps({"X3D": {
        "encoding": "UTF-8", "@profile": "Interchange", "@version": "4.0",
        "haed": {"meta": []},
        "Scene": {"-children": [{"Shape": {"-geometry": {"Box": {}}}}]},
    }})
    result = validate_json(bad)
    assert result["valid"] is False
    assert any("haed" in e for e in result["errors"])


def test_invalid_json_misspelled_meta():
    """Misspelled `meta` inside head."""
    bad = json.dumps({"X3D": {
        "encoding": "UTF-8", "@profile": "Interchange", "@version": "4.0",
        "head": {"mteta": []},
        "Scene": {"-children": [{"Shape": {"-geometry": {"Box": {}}}}]},
    }})
    result = validate_json(bad)
    assert result["valid"] is False
    assert any("mteta" in e for e in result["errors"])


def test_invalid_json_unknown_node_in_scene():
    """Unknown node name inside Scene.-children fails schema validation."""
    bad = json.dumps({"X3D": {
        "encoding": "UTF-8", "@profile": "Interchange", "@version": "4.0",
        "Scene": {"-children": [{"FakeNode": {}}]},
    }})
    result = validate_json(bad)
    assert result["valid"] is False


def test_invalid_json_wrong_version_type():
    """@version must be a string, not an integer."""
    bad = json.dumps({"X3D": {
        "encoding": "UTF-8", "@profile": "Interchange", "@version": 4,
        "Scene": {"-children": [{"Shape": {"-geometry": {"Box": {}}}}]},
    }})
    result = validate_json(bad)
    assert result["valid"] is False
    assert any("@version" in e or "version" in e for e in result["errors"])


def test_json_error_format_includes_path():
    """Error strings carry a 'path/to/field: message' shape so the LLM can act."""
    bad = json.dumps({"X3D": {
        "encoding": "UTF-8", "@profile": "Interchange", "@version": "4.0",
        "head": {"mteta": []},
        "Scene": {"-children": [{"Shape": {"-geometry": {"Box": {}}}}]},
    }})
    result = validate_json(bad)
    assert result["valid"] is False
    assert any(":" in e for e in result["errors"])
    assert any(e.startswith("X3D/head") or "head" in e for e in result["errors"])
