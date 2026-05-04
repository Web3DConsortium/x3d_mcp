"""X3D animation tools.

Generates TimeSensor + Interpolator + ROUTE chains for common animations,
validates and inserts individual ROUTE statements, and provides reference
documentation for X3D's event-driven animation system.

Adapted from animation.py in https://github.com/niknarra/x3d-mcp by
Nikhil Narra and Nicholas Polys (Virginia Tech / Web3D Consortium).
"""

from lxml import etree

from mcp.server.fastmcp import FastMCP

from tools.scene_ops import _parse_x3d_source, _find_scene
from x3d_utils.x3duom import get_x3duom


_INTERPOLATOR_MAP = {
    "SFRotation": {
        "node": "OrientationInterpolator",
        "value_changed_field": "value_changed",
    },
    "SFVec3f": {
        "node": "PositionInterpolator",
        "value_changed_field": "value_changed",
    },
    "SFVec2f": {
        "node": "PositionInterpolator2D",
        "value_changed_field": "value_changed",
    },
    "SFColor": {
        "node": "ColorInterpolator",
        "value_changed_field": "value_changed",
    },
    "SFFloat": {
        "node": "ScalarInterpolator",
        "value_changed_field": "value_changed",
    },
    "MFVec3f": {
        "node": "CoordinateInterpolator",
        "value_changed_field": "value_changed",
    },
    "MFVec2f": {
        "node": "CoordinateInterpolator2D",
        "value_changed_field": "value_changed",
    },
}

_INPUT_FIELD_ALIASES = {
    "rotation": "rotation",
    "translation": "translation",
    "scale": "scale",
    "diffuseColor": "diffuseColor",
    "emissiveColor": "emissiveColor",
    "transparency": "transparency",
    "position": "position",
    "orientation": "orientation",
}


def _serialize(tree: etree._Element) -> str:
    return etree.tostring(
        tree, xml_declaration=True, encoding="UTF-8", pretty_print=True
    ).decode()


def _local_tag(el: etree._Element) -> str:
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _animate(
    source: str,
    target_def: str,
    field_name: str,
    from_value: str,
    to_value: str,
    duration: float = 5.0,
    loop: bool = True,
) -> str:
    if not target_def:
        return "target_def is required -- the DEF name of the node to animate."
    if not field_name:
        return (
            "field_name is required -- the field to animate "
            "(e.g., 'rotation', 'translation', 'diffuseColor')."
        )
    if not from_value or not to_value:
        return "Both from_value and to_value are required (space-separated strings)."

    try:
        tree = _parse_x3d_source(source)
    except ValueError as e:
        return str(e)

    try:
        scene = _find_scene(tree)
    except ValueError as e:
        return str(e)

    matches = scene.xpath(f"//*[@DEF='{target_def}']")
    if not matches:
        all_defs = [el.get("DEF") for el in scene.xpath("//*[@DEF]")]
        if all_defs:
            return (
                f"No node with DEF='{target_def}' found. "
                f"Available DEF names: {', '.join(all_defs)}."
            )
        return (
            f"No node with DEF='{target_def}' found. The scene has no DEF'd nodes."
        )

    target_el = matches[0]
    target_type = _local_tag(target_el)

    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()
    target_node_info = nodes.get(target_type, {})
    all_fields = {f["name"]: f for f in target_node_info.get("fields", [])}
    field_info = all_fields.get(field_name)

    if field_info is None:
        animatable = sorted(
            f["name"] for f in all_fields.values()
            if f.get("accessType") in ("inputOutput", "inputOnly")
            and f.get("type") in _INTERPOLATOR_MAP
        )
        return (
            f"Field '{field_name}' not found on {target_type}. "
            f"Animatable fields: {', '.join(animatable[:15]) or '(none)'}."
        )

    field_type = field_info.get("type", "")
    interp_info = _INTERPOLATOR_MAP.get(field_type)
    if interp_info is None:
        return (
            f"Field '{field_name}' has type {field_type}, which does not have "
            f"a standard interpolator. Supported types: "
            f"{', '.join(sorted(_INTERPOLATOR_MAP.keys()))}."
        )

    access_type = field_info.get("accessType", "")
    if access_type not in ("inputOutput", "inputOnly"):
        return (
            f"Field '{field_name}' on {target_type} has accessType='{access_type}'. "
            f"Only inputOutput or inputOnly fields can be animation targets."
        )

    timer_def = f"{target_def}_{field_name}_Timer"
    interp_def = f"{target_def}_{field_name}_Interp"
    interp_node_type = interp_info["node"]

    timer_el = etree.SubElement(scene, "TimeSensor")
    timer_el.set("DEF", timer_def)
    timer_el.set("cycleInterval", str(duration))
    timer_el.set("loop", "true" if loop else "false")

    interp_el = etree.SubElement(scene, interp_node_type)
    interp_el.set("DEF", interp_def)
    interp_el.set("key", "0 1")
    interp_el.set("keyValue", f"{from_value}, {to_value}")

    route1 = etree.SubElement(scene, "ROUTE")
    route1.set("fromNode", timer_def)
    route1.set("fromField", "fraction_changed")
    route1.set("toNode", interp_def)
    route1.set("toField", "set_fraction")

    dest_field = _INPUT_FIELD_ALIASES.get(field_name, f"set_{field_name}")
    route2 = etree.SubElement(scene, "ROUTE")
    route2.set("fromNode", interp_def)
    route2.set("fromField", interp_info["value_changed_field"])
    route2.set("toNode", target_def)
    route2.set("toField", dest_field)

    return _serialize(tree)


def _add_route(
    source: str,
    from_node: str,
    from_field: str,
    to_node: str,
    to_field: str,
) -> str:
    if not all([from_node, from_field, to_node, to_field]):
        return "All four parameters are required: from_node, from_field, to_node, to_field."

    try:
        tree = _parse_x3d_source(source)
    except ValueError as e:
        return str(e)

    try:
        scene = _find_scene(tree)
    except ValueError as e:
        return str(e)

    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()

    def_map: dict[str, str] = {}
    for el in scene.iter():
        d = el.get("DEF")
        if d:
            def_map[d] = _local_tag(el)

    all_defs = sorted(def_map.keys())

    from_type = def_map.get(from_node)
    if from_type is None:
        return (
            f"fromNode DEF='{from_node}' not found in the scene. "
            f"Available DEFs: {', '.join(all_defs) or '(none)'}."
        )

    to_type = def_map.get(to_node)
    if to_type is None:
        return (
            f"toNode DEF='{to_node}' not found in the scene. "
            f"Available DEFs: {', '.join(all_defs) or '(none)'}."
        )

    from_fields = {f["name"]: f for f in nodes.get(from_type, {}).get("fields", [])}
    to_fields = {f["name"]: f for f in nodes.get(to_type, {}).get("fields", [])}

    from_field_info = from_fields.get(from_field)
    if from_field_info is None:
        return (
            f"fromField='{from_field}' does not exist on {from_type} (DEF='{from_node}')."
        )

    to_field_info = to_fields.get(to_field)
    if to_field_info is None:
        return (
            f"toField='{to_field}' does not exist on {to_type} (DEF='{to_node}')."
        )

    from_access = from_field_info.get("accessType", "")
    if from_access not in ("outputOnly", "inputOutput"):
        return (
            f"Cannot ROUTE from '{from_field}' on {from_type}: accessType is "
            f"'{from_access}', but must be 'outputOnly' or 'inputOutput'."
        )

    to_access = to_field_info.get("accessType", "")
    if to_access not in ("inputOnly", "inputOutput"):
        return (
            f"Cannot ROUTE to '{to_field}' on {to_type}: accessType is "
            f"'{to_access}', but must be 'inputOnly' or 'inputOutput'."
        )

    from_ft = from_field_info.get("type", "")
    to_ft = to_field_info.get("type", "")
    if from_ft and to_ft and from_ft != to_ft:
        return (
            f"ROUTE type mismatch: {from_node}.{from_field} is {from_ft} "
            f"but {to_node}.{to_field} is {to_ft}. ROUTE requires matching types."
        )

    route_el = etree.SubElement(scene, "ROUTE")
    route_el.set("fromNode", from_node)
    route_el.set("fromField", from_field)
    route_el.set("toNode", to_node)
    route_el.set("toField", to_field)

    return _serialize(tree)


def _animation_info(topic: str = "") -> str:
    t = topic.lower().strip()
    if t in ("interpolator", "interpolators"):
        return _interpolators_reference()
    if t in ("timesensor", "timer", "time"):
        return _timesensor_reference()
    if t in ("route", "routes", "routing"):
        return _routes_reference()
    if t in ("example", "examples", "patterns"):
        return _examples_reference()
    return _overview()


def _overview() -> str:
    return """\
# X3D Animation System Overview

X3D uses an **event-driven** animation system with three key components:

## 1. TimeSensor (the clock)
Generates a `fraction_changed` output (0.0 -> 1.0) over a `cycleInterval` duration.
Set `loop="true"` for continuous animation.

## 2. Interpolators (the value generators)
Take a fraction input (0-1) and output interpolated values based on `key`/`keyValue` pairs.
Each field type has a dedicated interpolator:
- **SFRotation** -> OrientationInterpolator
- **SFVec3f** -> PositionInterpolator (for translation, scale, etc.)
- **SFColor** -> ColorInterpolator
- **SFFloat** -> ScalarInterpolator (for transparency, intensity, etc.)
- **MFVec3f** -> CoordinateInterpolator (for morphing geometry)

## 3. ROUTE (the wiring)
Connects outputs to inputs:
```
TimeSensor.fraction_changed -> Interpolator.set_fraction
Interpolator.value_changed -> TargetNode.set_fieldName
```

## Quick Start
Use `animate_x3d_node` to generate a complete animation chain automatically.
Use `add_x3d_route` to add individual event connections.
Use `x3d_animation_info('examples')` for common patterns.
Use `x3d_animation_info('interpolators')` for the full interpolator reference."""


def _interpolators_reference() -> str:
    uom = get_x3duom()
    nodes = uom.get_concrete_nodes()

    interp_names = sorted(name for name in nodes if "Interpolator" in name)
    lines = [
        "# X3D Interpolator Nodes",
        "",
        f"Found {len(interp_names)} interpolator nodes:",
        "",
    ]
    for name in interp_names:
        comp = nodes[name].get("component", "")
        lines.append(f"- **{name}** [{comp}]")

    lines.extend([
        "",
        "## Common Mappings",
        "",
        "| Target Field Type | Interpolator | Example Fields |",
        "|---|---|---|",
        "| SFRotation | OrientationInterpolator | rotation, orientation |",
        "| SFVec3f | PositionInterpolator | translation, scale, position |",
        "| SFColor | ColorInterpolator | diffuseColor, emissiveColor |",
        "| SFFloat | ScalarInterpolator | transparency, intensity |",
        "| MFVec3f | CoordinateInterpolator | point (on Coordinate) |",
        "",
        "Use `animate_x3d_node` to auto-select the correct interpolator for a field.",
    ])
    return "\n".join(lines)


def _timesensor_reference() -> str:
    return """\
# TimeSensor Reference

TimeSensor is the animation clock in X3D.

## Key Fields
- **cycleInterval** (SFTime): Duration of one cycle in seconds. Default: 1.0
- **loop** (SFBool): Whether the timer repeats. Default: false
- **enabled** (SFBool): Whether the timer is active. Default: true
- **startTime** (SFTime): When to start (0 = scene load). Default: 0

## Key Outputs (for ROUTE)
- **fraction_changed** (SFFloat): 0.0 -> 1.0 over cycleInterval -- connect to Interpolator.set_fraction
- **time** (SFTime): Current time as the timer runs
- **cycleTime** (SFTime): Emitted at the start of each cycle
- **isActive** (SFBool): True while the timer is running

## Example
```xml
<TimeSensor DEF="Clock" cycleInterval="3" loop="true"/>
```

Use `animate_x3d_node` to automatically create TimeSensors wired to interpolators."""


def _routes_reference() -> str:
    return """\
# ROUTE Reference

ROUTEs connect event outputs to event inputs.

## Syntax
```xml
<ROUTE fromNode="SourceDEF" fromField="outputField"
       toNode="DestDEF" toField="inputField"/>
```

## Rules
1. **fromField** must have accessType `outputOnly` or `inputOutput`
2. **toField** must have accessType `inputOnly` or `inputOutput`
3. **Field types must match** (e.g., both SFVec3f, both SFFloat)
4. Both nodes must have **DEF names**
5. ROUTEs are placed at the **Scene level**

## Common Patterns
```xml
<ROUTE fromNode="Clock" fromField="fraction_changed"
       toNode="Mover" toField="set_fraction"/>
<ROUTE fromNode="Mover" fromField="value_changed"
       toNode="MyTransform" toField="translation"/>
```

Use `add_x3d_route` to validate and insert ROUTEs with type checking."""


def _examples_reference() -> str:
    return """\
# X3D Animation Examples

## 1. Continuous Rotation
```xml
<TimeSensor DEF="Spinner" cycleInterval="4" loop="true"/>
<OrientationInterpolator DEF="SpinInterp"
    key="0 0.5 1"
    keyValue="0 1 0 0, 0 1 0 3.14159, 0 1 0 6.28318"/>
<ROUTE fromNode="Spinner" fromField="fraction_changed"
       toNode="SpinInterp" toField="set_fraction"/>
<ROUTE fromNode="SpinInterp" fromField="value_changed"
       toNode="MyTransform" toField="rotation"/>
```

## 2. Color Pulse
```xml
<TimeSensor DEF="ColorTimer" cycleInterval="2" loop="true"/>
<ColorInterpolator DEF="ColorInterp"
    key="0 0.5 1"
    keyValue="1 0 0, 0 0 1, 1 0 0"/>
<ROUTE fromNode="ColorTimer" fromField="fraction_changed"
       toNode="ColorInterp" toField="set_fraction"/>
<ROUTE fromNode="ColorInterp" fromField="value_changed"
       toNode="MyMaterial" toField="diffuseColor"/>
```

## 3. Path Animation
```xml
<TimeSensor DEF="PathTimer" cycleInterval="8" loop="true"/>
<PositionInterpolator DEF="PathInterp"
    key="0 0.25 0.5 0.75 1"
    keyValue="0 0 0, 5 0 0, 5 0 5, 0 0 5, 0 0 0"/>
<ROUTE fromNode="PathTimer" fromField="fraction_changed"
       toNode="PathInterp" toField="set_fraction"/>
<ROUTE fromNode="PathInterp" fromField="value_changed"
       toNode="MyTransform" toField="translation"/>
```

**Tip:** Use `animate_x3d_node` to generate these patterns automatically."""


def register(mcp: FastMCP):

    @mcp.tool()
    def animate_x3d_node(
        content: str,
        target_def: str,
        field_name: str,
        from_value: str,
        to_value: str,
        duration: float = 5.0,
        loop: bool = True,
    ) -> str:
        """Insert a complete animation chain (TimeSensor + Interpolator + 2 ROUTEs)
        into an X3D document.

        The interpolator is auto-selected from the target field's type via
        X3DUOM lookup: SFRotation -> OrientationInterpolator,
        SFVec3f -> PositionInterpolator, SFColor -> ColorInterpolator,
        SFFloat -> ScalarInterpolator, etc.

        Args:
            content: X3D content (inline XML or file path).
            target_def: DEF name of the node whose field to animate.
            field_name: Field name on that node (must be inputOutput or inputOnly).
            from_value: Starting value (space-separated string).
            to_value: Ending value (space-separated string).
            duration: Cycle interval in seconds.
            loop: Whether the animation repeats.
        """
        return _animate(content, target_def, field_name, from_value, to_value,
                        duration, loop)

    @mcp.tool()
    def add_x3d_route(
        content: str,
        from_node: str,
        from_field: str,
        to_node: str,
        to_field: str,
    ) -> str:
        """Validate and insert a ROUTE statement into an X3D document.

        Verifies that both DEF names exist, both field names exist on the
        respective node types, access types are compatible (outputOnly/
        inputOutput on the source, inputOnly/inputOutput on the destination),
        and the field types match. Returns the modified X3D document, or
        an error message if any check fails.

        Args:
            content: X3D content (inline XML or file path).
            from_node: DEF of the source node.
            from_field: Field on the source node (must produce events).
            to_node: DEF of the destination node.
            to_field: Field on the destination node (must accept events).
        """
        return _add_route(content, from_node, from_field, to_node, to_field)

    @mcp.tool()
    def x3d_animation_info(topic: str = "") -> str:
        """Reference documentation for X3D's event-driven animation system.

        Args:
            topic: One of "interpolators", "timesensor", "routes", "examples".
                Empty/unknown returns the overview.
        """
        return _animation_info(topic)
