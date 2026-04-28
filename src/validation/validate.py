"""X3D validation pipeline.

Validates X3D content against the X3D 4.1 XSD schema using lxml,
and X3D JSON content against the Web3D Consortium X3D 4.0 JSON Schema
using jsonschema (Draft 2020-12).
"""

import json
from pathlib import Path
from lxml import etree
from jsonschema import Draft202012Validator


SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"
XSD_PATH = SCHEMAS_DIR / "x3d-4.1.xsd"
JSON_SCHEMA_PATH = SCHEMAS_DIR / "x3d-4.0-JSONSchema.json"

# XSI namespace attribute that x3d.py adds -- must be stripped before validation
XSI_NS = "https://www.w3.org/2001/XMLSchema-instance"

_schema = None
_json_validator: Draft202012Validator | None = None


def _get_schema() -> etree.XMLSchema:
    """Load and cache the X3D 4.1 XSD schema."""
    global _schema
    if _schema is not None:
        return _schema
    # Parse with the schemas dir as base so includes resolve correctly
    schema_doc = etree.parse(str(XSD_PATH))
    _schema = etree.XMLSchema(schema_doc)
    return _schema


def _strip_xsi(root: etree._Element) -> None:
    """Remove xsi namespace attributes that x3d.py injects."""
    for attr in list(root.attrib):
        if XSI_NS in attr:
            del root.attrib[attr]
    # Also remove the xsd namespace prefix declaration if present
    nsmap = dict(root.nsmap)
    if "xsd" in nsmap or "xsi" in nsmap:
        # Can't remove nsmap directly, so rebuild the element
        pass


def validate_xml(xml_string: str) -> dict:
    """Validate X3D XML content against the XSD schema.

    Returns {"valid": bool, "errors": list[str]}.
    """
    errors = []

    # Step 1: Parse XML (well-formedness)
    try:
        doc = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        return {"valid": False, "errors": [f"XML parse error: {e}"]}

    # Step 2: Strip xsi attributes that x3d.py adds
    _strip_xsi(doc)

    # Step 3: Validate against XSD
    schema = _get_schema()
    valid = schema.validate(doc)
    if not valid:
        for entry in schema.error_log:
            errors.append(f"Line {entry.line}: {entry.message}")

    return {"valid": valid, "errors": errors}


def validate_scene(scene_manager) -> dict:
    """Validate the current scene by serializing to XML and running XSD checks.

    Returns {"valid": bool, "errors": list[str]}.
    """
    xml_string = scene_manager.to_xml()
    return validate_xml(xml_string)


def _get_json_validator() -> Draft202012Validator:
    """Load and cache the X3D 4.0 JSON Schema validator."""
    global _json_validator
    if _json_validator is not None:
        return _json_validator
    with JSON_SCHEMA_PATH.open() as f:
        schema = json.load(f)
    _json_validator = Draft202012Validator(schema)
    return _json_validator


def _format_json_path(path) -> str:
    """Format a jsonschema absolute_path deque as 'X3D/head/meta/0' or '(root)'."""
    parts = [str(p) for p in path]
    return "/".join(parts) if parts else "(root)"


def validate_json(json_string: str) -> dict:
    """Validate X3D JSON content against the Web3D X3D 4.0 JSON Schema.

    Catches misspelled keys (head/meta/etc.), unknown nodes inside Scene,
    missing required fields, and wrong-type values via Draft 2020-12
    schema validation. Returns {"valid": bool, "errors": list[str]}.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"JSON parse error: {e}"]}

    validator = _get_json_validator()
    errors = [
        f"{_format_json_path(err.absolute_path)}: {err.message}"
        for err in validator.iter_errors(data)
    ]
    return {"valid": len(errors) == 0, "errors": errors}
