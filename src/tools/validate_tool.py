"""X3D validation MCP tools.

Exposes validation pipeline as MCP tools.
"""

import json
from mcp.server.fastmcp import FastMCP

from validation.validate import validate_xml, validate_json
from validation.semantic import validate_semantic as _validate_semantic
from tools.granular import _scene


def register(mcp: FastMCP):

    @mcp.tool()
    def validate_x3d(content: str, encoding: str = "xml") -> str:
        """Validate X3D content against the X3D 4.1 schema.

        Args:
            content: The X3D content string to validate.
            encoding: Content encoding - "xml" or "json".
        """
        if encoding == "xml":
            result = validate_xml(content)
        elif encoding == "json":
            result = validate_json(content)
        else:
            result = {"valid": False, "errors": [f"Unsupported encoding: {encoding}"]}
        return json.dumps(result, indent=2)

    @mcp.tool()
    def validate_current_scene() -> str:
        """Validate the current granular scene against the X3D 4.1 schema."""
        xml_content = _scene.to_xml()
        result = validate_xml(xml_content)
        return json.dumps(result, indent=2)

    @mcp.tool()
    def validate_semantic(content: str) -> str:
        """Run semantic checks on X3D XML content beyond XSD schema validation.

        Detects common authoring issues that XSD cannot catch: missing geometry
        on Shapes, empty grouping nodes, duplicate DEFs, USE references to
        non-existent DEFs, ROUTE field/type/access-type problems, and missing
        Viewpoints. Returns a markdown report.

        Args:
            content: The X3D XML content string to check.
        """
        return _validate_semantic(content)
