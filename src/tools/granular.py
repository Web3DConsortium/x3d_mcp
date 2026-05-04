"""Granular X3D scene building tools.

Provides node-by-node scene construction tools for precise control
over the X3D scene graph.
"""

from mcp.server.fastmcp import FastMCP

from x3d_utils.scene import SceneManager


_scene = SceneManager()


def register(mcp: FastMCP):

    @mcp.tool()
    def create_node(node_type: str, fields: dict | None = None) -> str:
        """Create a new X3D node and return its tracking ID.

        Args:
            node_type: The X3D node type (e.g. "Box", "Material", "Transform").
            fields: Optional dict of field name -> value pairs to set on creation.
        """
        kwargs = fields or {}
        node_id = _scene.create_node(node_type, **kwargs)
        return f"Created {node_type} with ID: {node_id}"

    @mcp.tool()
    def set_field(node_id: str, field_name: str,
                  value: str | int | float | list) -> str:
        """Set a field value on an existing node.

        Args:
            node_id: The node tracking ID returned by create_node.
            field_name: The field name (e.g. "diffuseColor", "size", "translation").
            value: The value to set. Use lists for vector types.
        """
        if isinstance(value, list):
            value = tuple(value)
        _scene.set_field(node_id, field_name, value)
        return f"Set {field_name} on {node_id}"

    @mcp.tool()
    def add_child(parent_id: str, child_id: str) -> str:
        """Add a child node to a parent node in the scene graph.

        Args:
            parent_id: The parent node tracking ID.
            child_id: The child node tracking ID.
        """
        _scene.add_child(parent_id, child_id)
        return f"Added {child_id} as child of {parent_id}"

    @mcp.tool()
    def add_route(from_node: str, from_field: str,
                  to_node: str, to_field: str) -> str:
        """Add a ROUTE connecting two node fields for event propagation.

        Args:
            from_node: Source node tracking ID (must have a DEF name).
            from_field: Source field name (e.g. "fraction_changed").
            to_node: Target node tracking ID (must have a DEF name).
            to_field: Target field name (e.g. "set_fraction").
        """
        _scene.add_route(from_node, from_field, to_node, to_field)
        return f"Added ROUTE from {from_node}.{from_field} to {to_node}.{to_field}"

    @mcp.tool()
    def def_node(node_id: str, name: str) -> str:
        """Assign a DEF name to a node for referencing via USE or ROUTE.

        Args:
            node_id: The node tracking ID.
            name: The DEF name to assign (must be unique in the scene).
        """
        _scene.def_node(node_id, name)
        return f"Assigned DEF '{name}' to {node_id}"

    @mcp.tool()
    def use_node(def_name: str) -> str:
        """Create a USE reference to a previously DEF'd node.

        Args:
            def_name: The DEF name of the node to reference.
        """
        node_id = _scene.use_node(def_name)
        return f"Created USE reference to '{def_name}' with ID: {node_id}"

    @mcp.tool()
    def remove_node(node_id: str) -> str:
        """Remove a node and its children from the scene.

        Args:
            node_id: The node tracking ID to remove.
        """
        _scene.remove_node(node_id)
        return f"Removed node {node_id}"

    @mcp.tool()
    def get_scene(encoding: str = "xml") -> str:
        """Get the current scene in the specified encoding.

        Args:
            encoding: Output encoding - "xml", "json", or "vrml".
        """
        if encoding == "xml":
            return _scene.to_xml()
        elif encoding == "json":
            return _scene.to_json()
        elif encoding == "vrml":
            return _scene.to_vrml()
        else:
            return f"Unknown encoding: {encoding}. Use 'xml', 'json', or 'vrml'."

    @mcp.tool()
    def reset_scene() -> str:
        """Clear all nodes and reset the scene to empty state."""
        _scene.reset()
        return "Scene reset to empty state"
