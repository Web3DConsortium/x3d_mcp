"""Semantic validation for X3D scenes beyond XSD schema checks.

Detects common authoring issues that XSD cannot catch: missing geometry,
unused DEFs, broken ROUTE references, empty groups, duplicate DEF names,
and missing viewpoints.

Adapted from semantic_check.py in https://github.com/niknarra/x3d-mcp by
Nikhil Narra and Nicholas Polys (Virginia Tech / Web3D Consortium).
"""

from dataclasses import dataclass
from lxml import etree

from x3d_utils.x3duom import get_x3duom


_GROUPING_NODES = {
    "Transform", "Group", "Switch", "Collision", "LOD", "Anchor",
    "Billboard", "StaticGroup", "CADAssembly", "CADLayer", "CADPart",
    "GeoLOD", "EspduTransform", "ReceiverPdu", "SignalPdu",
    "TransmitterPdu", "HAnimJoint", "HAnimSegment", "HAnimSite",
    "LayoutGroup", "ScreenGroup", "Viewport",
}

_GEOMETRY_NODES: set[str] | None = None


def _get_geometry_nodes() -> set[str]:
    """Return the set of concrete node names that can serve as geometry in a Shape.

    Walks X3DUOM inheritance to find every node ultimately based on
    X3DGeometryNode, then unions a hardcoded core set for safety.
    """
    global _GEOMETRY_NODES
    if _GEOMETRY_NODES is not None:
        return _GEOMETRY_NODES

    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    abstracts = uom.get_abstract_types()

    geometry_types: set[str] = set()
    for name, info in nodes.items():
        if _inherits_from(info, "X3DGeometryNode", nodes, abstracts):
            geometry_types.add(name)

    geometry_types.update({
        "Box", "Sphere", "Cylinder", "Cone", "Text",
        "IndexedFaceSet", "IndexedLineSet", "IndexedTriangleSet",
        "PointSet", "LineSet", "TriangleSet",
        "ElevationGrid", "Extrusion",
    })

    _GEOMETRY_NODES = geometry_types
    return _GEOMETRY_NODES


def _inherits_from(info: dict, target: str, nodes: dict, abstracts: dict,
                   visited: set | None = None) -> bool:
    """Walk the baseType chain to determine if a node inherits from target."""
    if visited is None:
        visited = set()
    base = info.get("baseType")
    if not base or base in visited:
        return False
    visited.add(base)
    if base == target:
        return True
    parent = abstracts.get(base) or nodes.get(base)
    if parent is None:
        return False
    return _inherits_from(parent, target, nodes, abstracts, visited)


@dataclass
class Diagnostic:
    level: str
    check: str
    message: str
    node_tag: str = ""
    def_name: str = ""


def _local_tag(el: etree._Element) -> str:
    """Strip XML namespace prefix from an element tag."""
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _check_duplicate_defs(scene: etree._Element) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: dict[str, str] = {}
    for el in scene.iter():
        def_name = el.get("DEF")
        if not def_name:
            continue
        tag = _local_tag(el)
        if def_name in seen:
            diagnostics.append(Diagnostic(
                level="error",
                check="duplicate-def",
                message=f"Duplicate DEF name '{def_name}': first used on {seen[def_name]}, "
                        f"also used on {tag}. DEF names must be unique within a scene.",
                node_tag=tag,
                def_name=def_name,
            ))
        else:
            seen[def_name] = tag
    return diagnostics


def _check_def_use_consistency(scene: etree._Element) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    defs: dict[str, str] = {}
    uses: set[str] = set()
    for el in scene.iter():
        tag = _local_tag(el)
        def_name = el.get("DEF")
        if def_name and def_name not in defs:
            defs[def_name] = tag
        use_name = el.get("USE")
        if use_name:
            uses.add(use_name)

    for use_name in sorted(uses):
        if use_name not in defs:
            available = ", ".join(sorted(defs.keys())) or "(none)"
            diagnostics.append(Diagnostic(
                level="error",
                check="use-undefined-def",
                message=f"USE='{use_name}' references a DEF that does not exist in this scene. "
                        f"Available DEF names: {available}.",
                def_name=use_name,
            ))

    for def_name in sorted(set(defs.keys()) - uses):
        diagnostics.append(Diagnostic(
            level="info",
            check="unused-def",
            message=f"DEF='{def_name}' ({defs[def_name]}) is defined but never USE'd. "
                    f"This is fine if you reference it via ROUTE or externally.",
            node_tag=defs[def_name],
            def_name=def_name,
        ))

    return diagnostics


def _check_shape_completeness(scene: etree._Element) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    geometry_nodes = _get_geometry_nodes()
    for shape in scene.iter("Shape"):
        def_name = shape.get("DEF", "")
        child_tags = {_local_tag(child) for child in shape}
        has_geometry = bool(child_tags & geometry_nodes)
        has_appearance = "Appearance" in child_tags
        label = f" (DEF={def_name!r})" if def_name else ""
        if not has_geometry:
            diagnostics.append(Diagnostic(
                level="warning",
                check="shape-no-geometry",
                message=f"Shape{label} has no geometry child. "
                        f"Add a geometry node like Box, Sphere, or IndexedFaceSet.",
                node_tag="Shape",
                def_name=def_name,
            ))
        if not has_appearance:
            diagnostics.append(Diagnostic(
                level="info",
                check="shape-no-appearance",
                message=f"Shape{label} has no Appearance. "
                        f"The shape will render with a default white material.",
                node_tag="Shape",
                def_name=def_name,
            ))
    return diagnostics


def _check_empty_groups(scene: etree._Element) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for tag in _GROUPING_NODES:
        for el in scene.iter(tag):
            if len(el) == 0:
                if el.get("USE"):
                    # A USE reference reuses the DEF'd node wholesale; it is
                    # intentionally childless and not an empty group.
                    continue
                def_name = el.get("DEF", "")
                label = f" (DEF={def_name!r})" if def_name else ""
                diagnostics.append(Diagnostic(
                    level="warning",
                    check="empty-group",
                    message=f"{tag}{label} has no children. "
                            f"Empty grouping nodes have no effect.",
                    node_tag=tag,
                    def_name=def_name,
                ))
    return diagnostics


def _resolve_route_field(fields: dict, field_name: str, direction: str) -> dict | None:
    """Look up a ROUTE field, honoring X3D event-model aliases.

    Every inputOutput field X implicitly provides an inputOnly set_X and an
    outputOnly X_changed (ISO 19775-1 clause 4.4.2.2), so ROUTEs may name
    either form. direction is "in" for toField, "out" for fromField.
    """
    info = fields.get(field_name)
    if info is not None:
        return info
    if direction == "in" and field_name.startswith("set_"):
        base = fields.get(field_name[len("set_"):])
        if base is not None and base.get("accessType") == "inputOutput":
            return base
    if direction == "out" and field_name.endswith("_changed"):
        base = fields.get(field_name[: -len("_changed")])
        if base is not None and base.get("accessType") == "inputOutput":
            return base
    return None


def _check_route_validity(scene: etree._Element) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()

    def_map: dict[str, tuple[etree._Element, str]] = {}
    for el in scene.iter():
        def_name = el.get("DEF")
        if def_name:
            def_map[def_name] = (el, _local_tag(el))

    for route in scene.iter("ROUTE"):
        from_node = route.get("fromNode", "")
        from_field = route.get("fromField", "")
        to_node = route.get("toNode", "")
        to_field = route.get("toField", "")

        if from_node not in def_map:
            available = ", ".join(sorted(def_map.keys())) or "(none)"
            diagnostics.append(Diagnostic(
                level="error",
                check="route-missing-from-node",
                message=f"ROUTE fromNode='{from_node}' not found. "
                        f"Available DEFs: {available}.",
            ))
            continue

        if to_node not in def_map:
            available = ", ".join(sorted(def_map.keys())) or "(none)"
            diagnostics.append(Diagnostic(
                level="error",
                check="route-missing-to-node",
                message=f"ROUTE toNode='{to_node}' not found. "
                        f"Available DEFs: {available}.",
            ))
            continue

        _, from_type = def_map[from_node]
        _, to_type = def_map[to_node]

        from_fields = {f["name"]: f for f in nodes.get(from_type, {}).get("fields", [])}
        to_fields = {f["name"]: f for f in nodes.get(to_type, {}).get("fields", [])}

        from_field_info = _resolve_route_field(from_fields, from_field, "out")
        if from_field_info is None:
            diagnostics.append(Diagnostic(
                level="error",
                check="route-invalid-from-field",
                message=f"ROUTE fromField='{from_field}' does not exist on {from_type} "
                        f"(DEF='{from_node}').",
            ))
            continue

        to_field_info = _resolve_route_field(to_fields, to_field, "in")
        if to_field_info is None:
            diagnostics.append(Diagnostic(
                level="error",
                check="route-invalid-to-field",
                message=f"ROUTE toField='{to_field}' does not exist on {to_type} "
                        f"(DEF='{to_node}').",
            ))
            continue

        from_access = from_field_info.get("accessType", "")
        if from_access not in ("outputOnly", "inputOutput"):
            diagnostics.append(Diagnostic(
                level="error",
                check="route-wrong-access-type",
                message=f"ROUTE fromField='{from_field}' on {from_type} has "
                        f"accessType='{from_access}' -- must be 'outputOnly' or "
                        f"'inputOutput' to be a ROUTE source.",
            ))

        to_access = to_field_info.get("accessType", "")
        if to_access not in ("inputOnly", "inputOutput"):
            diagnostics.append(Diagnostic(
                level="error",
                check="route-wrong-access-type",
                message=f"ROUTE toField='{to_field}' on {to_type} has "
                        f"accessType='{to_access}' -- must be 'inputOnly' or "
                        f"'inputOutput' to be a ROUTE destination.",
            ))

        from_type_name = from_field_info.get("type", "")
        to_type_name = to_field_info.get("type", "")
        if from_type_name and to_type_name and from_type_name != to_type_name:
            diagnostics.append(Diagnostic(
                level="error",
                check="route-type-mismatch",
                message=f"ROUTE type mismatch: {from_node}.{from_field} is {from_type_name} "
                        f"but {to_node}.{to_field} is {to_type_name}. "
                        f"ROUTE requires matching field types.",
            ))

    return diagnostics


def _check_missing_viewpoint(scene: etree._Element) -> list[Diagnostic]:
    if list(scene.iter("Viewpoint")):
        return []
    return [Diagnostic(
        level="info",
        check="no-viewpoint",
        message="Scene has no Viewpoint node. The browser will use a default camera. "
                "Consider adding a Viewpoint for a defined initial view.",
    )]


_ALL_CHECKS = [
    _check_duplicate_defs,
    _check_def_use_consistency,
    _check_shape_completeness,
    _check_empty_groups,
    _check_route_validity,
    _check_missing_viewpoint,
]


def _find_scene(root: etree._Element) -> etree._Element | None:
    """Find the Scene element under the X3D root, namespace-tolerant."""
    if _local_tag(root) == "Scene":
        return root
    for child in root.iter():
        if _local_tag(child) == "Scene":
            return child
    return None


def validate_semantic(xml_string: str) -> str:
    """Run all semantic checks on an X3D XML string and return a markdown report."""
    try:
        root = etree.fromstring(xml_string.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        return f"# Semantic Check: Parse Error\n\n{e}"

    scene = _find_scene(root)
    if scene is None:
        return "# Semantic Check: No Scene\n\nNo Scene element found in the X3D document."

    all_diagnostics: list[Diagnostic] = []
    for check_fn in _ALL_CHECKS:
        all_diagnostics.extend(check_fn(scene))

    if not all_diagnostics:
        return (
            "# Semantic Check: All Clear\n\n"
            "No semantic issues found. The scene looks well-structured.\n"
            "Note: This checks common authoring issues beyond XSD schema validation. "
            "Use validate_x3d for schema-level validation."
        )

    errors = [d for d in all_diagnostics if d.level == "error"]
    warnings = [d for d in all_diagnostics if d.level == "warning"]
    infos = [d for d in all_diagnostics if d.level == "info"]

    lines = [
        "# Semantic Check Report",
        "",
        f"Found {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info(s).",
        "",
    ]

    if errors:
        lines.append("## Errors")
        lines.append("")
        for d in errors:
            lines.append(f"- **[{d.check}]** {d.message}")
        lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for d in warnings:
            lines.append(f"- **[{d.check}]** {d.message}")
        lines.append("")

    if infos:
        lines.append("## Info")
        lines.append("")
        for d in infos:
            lines.append(f"- **[{d.check}]** {d.message}")

    return "\n".join(lines)
