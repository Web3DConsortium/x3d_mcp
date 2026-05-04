"""X3D scene manipulation tools: modify, remove, and move nodes.

Operates on serialized X3D content (file path or inline XML) and returns
the modified XML string. Distinct from the granular tools in
``tools/granular.py`` which mutate the in-memory SceneManager state.

Adapted from scene_manipulation.py in https://github.com/niknarra/x3d-mcp by
Nikhil Narra and Nicholas Polys (Virginia Tech / Web3D Consortium).
"""

import json
import os
from lxml import etree

from mcp.server.fastmcp import FastMCP


def _parse_x3d_source(source: str) -> etree._Element:
    """Parse an X3D source (file path or inline XML string) into an lxml tree.

    Raises ValueError with a descriptive message on failure.
    """
    stripped = source.strip()

    if (stripped.startswith("<?xml") or stripped.startswith("<X3D")
            or stripped.startswith("<!DOCTYPE")):
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            return etree.fromstring(stripped.encode(), parser)
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid X3D XML: {e}")

    if not os.path.exists(stripped):
        raise ValueError(
            f"File not found: {stripped}. "
            "Provide either an absolute file path to a .x3d file or inline X3D XML."
        )

    if not stripped.lower().endswith(".x3d"):
        raise ValueError(
            f"Unsupported file extension: {os.path.splitext(stripped)[1]}. "
            "Only XML-encoded X3D files (.x3d) are supported."
        )

    try:
        with open(stripped, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise ValueError(f"Could not read file '{stripped}': {e}")

    try:
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.fromstring(content.encode(), parser)
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML in file '{stripped}': {e}")


def _find_scene(tree: etree._Element) -> etree._Element:
    """Find the <Scene> element in a parsed X3D tree."""
    scene = tree.find("Scene")
    if scene is None:
        raise ValueError(
            "No <Scene> element found in the X3D document. "
            "A valid X3D document requires <X3D><Scene>...</Scene></X3D>."
        )
    return scene


def _serialize(tree: etree._Element) -> str:
    return etree.tostring(
        tree, xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode()


def _find_node_by_def(scene: etree._Element, def_name: str) -> etree._Element | None:
    matches = scene.xpath(f"//*[@DEF='{def_name}']")
    return matches[0] if matches else None


def _find_node_by_type(
    scene: etree._Element, node_type: str, index: int
) -> tuple[etree._Element | None, str]:
    matches = list(scene.iter(node_type))
    if not matches:
        return None, (
            f"No '{node_type}' node found in the scene. "
            f"Use list_nodes to see which node types exist in X3D."
        )
    if index >= len(matches):
        return None, (
            f"Index {index} out of range. The scene contains {len(matches)} "
            f"'{node_type}' node(s) (valid indices: 0-{len(matches) - 1})."
        )
    return matches[index], ""


def _available_defs(scene: etree._Element) -> list[str]:
    return [el.get("DEF") for el in scene.xpath("//*[@DEF]")]


def _is_descendant_of(node: etree._Element, ancestor: etree._Element) -> bool:
    parent = node.getparent()
    while parent is not None:
        if parent is ancestor:
            return True
        parent = parent.getparent()
    return False


def _modify_node(source: str, def_name: str, field_changes: dict) -> str:
    if not def_name:
        return "A def_name is required to identify the node to modify."
    if not field_changes:
        return "No field_changes provided. Pass a dict of field=value pairs to modify."

    try:
        tree = _parse_x3d_source(source)
    except ValueError as e:
        return str(e)

    try:
        scene = _find_scene(tree)
    except ValueError as e:
        return str(e)

    target = _find_node_by_def(scene, def_name)
    if target is None:
        defs = _available_defs(scene)
        if defs:
            return (
                f"No node with DEF='{def_name}' found. "
                f"Available DEF names: {', '.join(defs)}."
            )
        return (
            f"No node with DEF='{def_name}' found. The scene has no DEF'd nodes."
        )

    for field_name, value in field_changes.items():
        target.set(field_name, str(value))

    return _serialize(tree)


def _remove_node(
    source: str, def_name: str = "", node_type: str = "", index: int = 0
) -> str:
    if not def_name and not node_type:
        return (
            "Specify either def_name or node_type to identify the node to remove."
        )

    try:
        tree = _parse_x3d_source(source)
    except ValueError as e:
        return str(e)

    try:
        scene = _find_scene(tree)
    except ValueError as e:
        return str(e)

    if def_name:
        target = _find_node_by_def(scene, def_name)
        if target is None:
            defs = _available_defs(scene)
            if defs:
                return (
                    f"No node with DEF='{def_name}' found. "
                    f"Available DEF names: {', '.join(defs)}"
                )
            return (
                f"No node with DEF='{def_name}' found. The scene has no DEF'd nodes."
            )
    else:
        target, error = _find_node_by_type(scene, node_type, index)
        if target is None:
            return error

    if target is scene:
        return "Cannot remove the <Scene> element itself."

    parent = target.getparent()
    if parent is None:
        return "Cannot remove the root element."

    parent.remove(target)
    return _serialize(tree)


def _move_node(source: str, def_name: str, new_parent_def: str = "") -> str:
    if not def_name:
        return "A def_name is required to identify the node to move."

    try:
        tree = _parse_x3d_source(source)
    except ValueError as e:
        return str(e)

    try:
        scene = _find_scene(tree)
    except ValueError as e:
        return str(e)

    target = _find_node_by_def(scene, def_name)
    if target is None:
        defs = _available_defs(scene)
        if defs:
            return (
                f"No node with DEF='{def_name}' found. "
                f"Available DEF names: {', '.join(defs)}"
            )
        return (
            f"No node with DEF='{def_name}' found. The scene has no DEF'd nodes."
        )

    if new_parent_def:
        if new_parent_def == def_name:
            return f"Cannot move a node under itself (DEF='{def_name}')."

        new_parent = _find_node_by_def(scene, new_parent_def)
        if new_parent is None:
            defs = _available_defs(scene)
            return (
                f"New parent DEF='{new_parent_def}' not found. "
                f"Available DEF names: {', '.join(defs)}"
            )

        if _is_descendant_of(new_parent, target):
            return (
                f"Cannot move DEF='{def_name}' under DEF='{new_parent_def}' -- "
                f"'{new_parent_def}' is a descendant of '{def_name}', which would "
                f"create a cycle in the scene graph."
            )
    else:
        new_parent = scene

    old_parent = target.getparent()
    if old_parent is None:
        return "Cannot move the root element."

    if old_parent is new_parent:
        location = "<Scene>" if new_parent is scene else f"DEF={new_parent_def!r}"
        return f"Node DEF='{def_name}' is already a child of {location}."

    old_parent.remove(target)
    new_parent.append(target)

    return _serialize(tree)


def register(mcp: FastMCP):

    @mcp.tool()
    def modify_x3d_node(
        content: str, def_name: str, field_changes: str
    ) -> str:
        """Modify attribute values on a DEF'd node in an X3D document.

        Updates one or more field values on the named node and returns the
        complete modified X3D document. Operates on serialized X3D content
        (file path or inline XML); does not touch the granular scene state.

        Args:
            content: X3D content (inline XML string or file path to .x3d).
            def_name: DEF name of the node to modify.
            field_changes: JSON object string of {field_name: value} pairs,
                e.g. '{"diffuseColor": "0 1 0"}'.
        """
        try:
            changes = json.loads(field_changes) if field_changes else {}
        except json.JSONDecodeError as e:
            return f"Invalid JSON in field_changes: {e}"
        return _modify_node(content, def_name, changes)

    @mcp.tool()
    def remove_x3d_node(
        content: str,
        def_name: str = "",
        node_type: str = "",
        index: int = 0,
    ) -> str:
        """Remove a node (and its children) from an X3D document.

        Identify the target either by DEF name OR by node_type plus index.
        Returns the modified X3D document.

        Args:
            content: X3D content (inline XML string or file path to .x3d).
            def_name: DEF name of the node to remove (preferred).
            node_type: Node type name (e.g. 'Transform') if no DEF.
            index: 0-based index among nodes of that type.
        """
        return _remove_node(content, def_name, node_type, index)

    @mcp.tool()
    def move_x3d_node(
        content: str, def_name: str, new_parent_def: str = ""
    ) -> str:
        """Reparent a DEF'd node in an X3D document.

        If new_parent_def is empty, moves the node to be a direct child of
        <Scene>. Rejects moves that would create a cycle (moving a node
        under one of its own descendants) or move a node under itself.

        Args:
            content: X3D content (inline XML string or file path to .x3d).
            def_name: DEF name of the node to move.
            new_parent_def: DEF name of the new parent (empty = Scene root).
        """
        return _move_node(content, def_name, new_parent_def)
