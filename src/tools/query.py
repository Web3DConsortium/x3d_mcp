"""X3D metadata query tools.

Provides tools for querying node types, fields, components, and profiles
from the X3D Unified Object Model.
"""

import json
from mcp.server.fastmcp import FastMCP

from x3d_utils.x3duom import get_x3duom


def register(mcp: FastMCP):

    @mcp.tool()
    def list_nodes(component: str | None = None) -> str:
        """List available X3D node types, optionally filtered by component.

        Args:
            component: Filter by component name (e.g. "Geometry3D", "Shape").
                      If None, returns all 260 concrete nodes grouped by component.
        """
        uom = get_x3duom()
        if component:
            components = uom.get_components()
            if component not in components:
                return json.dumps({"error": f"Unknown component: {component}"})
            nodes = components[component]
            return json.dumps({"component": component, "nodes": nodes})
        else:
            components = uom.get_components()
            result = {}
            for comp, nodes in sorted(components.items()):
                result[comp] = nodes
            return json.dumps(result, indent=2)

    @mcp.tool()
    def describe_node(node_type: str) -> str:
        """Get detailed information about an X3D node type including all fields.

        Args:
            node_type: The node type name (e.g. "Box", "Material", "Transform").
        """
        uom = get_x3duom()
        enriched = uom.get_enriched_node(node_type)
        if enriched is None:
            return json.dumps({"error": f"Unknown node type: {node_type}"})

        fields = []
        for f in enriched["fields"]:
            field_info = {
                "name": f["name"],
                "type": f["type"],
                "accessType": f["accessType"],
                "default": f["default"],
            }
            if f.get("description"):
                field_info["description"] = f["description"]
            if f.get("inheritedFrom"):
                field_info["inheritedFrom"] = f["inheritedFrom"]
            if f.get("acceptableNodeTypes"):
                field_info["acceptableNodeTypes"] = f["acceptableNodeTypes"]
            if f.get("minInclusive"):
                field_info["minInclusive"] = f["minInclusive"]
            if f.get("maxInclusive"):
                field_info["maxInclusive"] = f["maxInclusive"]
            if f.get("tooltip"):
                field_info["tooltip"] = f["tooltip"]
            if f.get("hints"):
                field_info["hints"] = f["hints"]
            if f.get("warnings"):
                field_info["warnings"] = f["warnings"]
            if f.get("specUrls"):
                field_info["specUrls"] = f["specUrls"]
            fields.append(field_info)

        result = {
            "name": node_type,
            "component": enriched["component"],
            "level": enriched["level"],
            "baseType": enriched["baseType"],
            "containerField": enriched["containerField"],
            "fields": fields,
        }
        if enriched.get("tooltip"):
            result["tooltip"] = enriched["tooltip"]
        if enriched.get("hints"):
            result["hints"] = enriched["hints"]
        if enriched.get("warnings"):
            result["warnings"] = enriched["warnings"]
        if enriched.get("specUrls"):
            result["specUrls"] = enriched["specUrls"]

        return json.dumps(result, indent=2)

    @mcp.tool()
    def list_components() -> str:
        """List all X3D components and the number of nodes in each."""
        uom = get_x3duom()
        components = uom.get_components()
        result = {}
        for comp, nodes in sorted(components.items()):
            result[comp] = {"count": len(nodes), "nodes": nodes}
        return json.dumps(result, indent=2)

    @mcp.tool()
    def list_profiles() -> str:
        """List all X3D profiles."""
        uom = get_x3duom()
        profiles = uom.get_profiles()
        return json.dumps(profiles, indent=2)
