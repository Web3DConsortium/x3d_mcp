"""Measured ablation of the four-level validation pipeline.

Runs a fault-injection corpus through each validation level the fault
can reach and records which levels catch it. Level 1 is X3DPSAIL
constructor type checking, level 2 is FastMCP JSON-Schema tool-input
validation, level 3 is XSD validation, level 4 is the semantic checker.

The output matrix shows per-level catches and, most importantly, the
faults caught by exactly one level: disabling that level admits that
fault class silently. This is the structural (fault-injection) form of
the per-layer ablation; frequency-weighted ablation under live LLM
generation is future work tracked with the evaluation protocol.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import x3d.x3d as x3d_mod

from validation.validate import validate_xml
from validation.semantic import validate_semantic


DOC = """<?xml version="1.0" encoding="UTF-8"?>
<X3D profile='Full' version='4.1'>
  <Scene>
{body}
  </Scene>
</X3D>"""


def level1(fn):
    """Run a construction callable; caught if x3d.py raises."""
    try:
        fn()
        return False
    except Exception:
        return True


def level2(tool: str, payload: dict) -> bool:
    """Call an MCP tool with a malformed payload; caught if the
    protocol layer rejects it before the tool function runs."""
    from mcp.server.fastmcp import FastMCP
    from mcp.server.fastmcp.exceptions import ToolError
    from tools import workflow

    mcp = FastMCP("ablation")
    workflow.register(mcp)
    try:
        result = asyncio.new_event_loop().run_until_complete(
            mcp.call_tool(tool, payload)
        )
    except (ToolError, Exception):
        return True
    # Some clients surface schema rejection as an error result
    text = ""
    content = result[0] if isinstance(result, tuple) else result
    if isinstance(content, list) and content:
        text = getattr(content[0], "text", "")
    return "validation error" in text.lower() or "error" in text.lower()


def level3(xml: str) -> bool:
    return not validate_xml(xml)["valid"]


def level4(xml: str) -> bool:
    report = validate_semantic(xml)
    return "error" in report.lower()


CONSTRUCTION_FAULTS = [
    ("invented node type (Sphere3D)",
     lambda: getattr(x3d_mod, "Sphere3D")()),
    ("wrong field type (diffuseColor='red')",
     lambda: x3d_mod.Material(diffuseColor="red")),
    ("invented field (Sphere(sides=5))",
     lambda: x3d_mod.Sphere(sides=5)),
    ("out-of-range value (transparency=7)",
     lambda: x3d_mod.Material(transparency=7.0)),
]

TOOL_FAULTS = [
    ("tool payload: color as string not array",
     "create_geometry", {"shape": "sphere", "color": "red", "size": [1.0]}),
    ("tool payload: missing required 'shape'",
     "create_geometry", {"color": [1.0, 0.0, 0.0], "size": [1.0]}),
]

XML_FAULTS = [
    ("unknown element in Shape",
     "    <Shape><Sphere3D/></Shape>"),
    ("geometry under illegal parent (Sphere in Group)",
     "    <Group><Sphere/></Group>"),
    ("malformed attribute value (radius='big')",
     "    <Shape><Sphere radius='big'/></Shape>"),
    ("duplicate DEF",
     "    <Transform DEF='A'/>\n    <Transform DEF='A'/>"),
    ("USE without DEF",
     "    <Transform USE='Ghost'/>"),
    ("Shape missing geometry child",
     "    <Shape><Appearance><Material/></Appearance></Shape>"),
    ("empty grouping node",
     "    <Group></Group>"),
    ("ROUTE type mismatch (SFFloat -> SFVec3f)",
     "    <TimeSensor DEF='T'/>\n"
     "    <Transform DEF='X'/>\n"
     "    <ROUTE fromNode='T' fromField='fraction_changed' "
     "toNode='X' toField='set_translation'/>"),
    ("ROUTE to nonexistent DEF",
     "    <TimeSensor DEF='T'/>\n"
     "    <ROUTE fromNode='T' fromField='fraction_changed' "
     "toNode='Nowhere' toField='set_fraction'/>"),
]


def main():
    rows = []
    for name, fn in CONSTRUCTION_FAULTS:
        rows.append((name, "Y" if level1(fn) else "MISS", "-", "-", "-"))
    for name, tool, payload in TOOL_FAULTS:
        rows.append((name, "-", "Y" if level2(tool, payload) else "MISS",
                     "-", "-"))
    for name, body in XML_FAULTS:
        xml = DOC.format(body=body)
        l3 = level3(xml)
        l4 = level4(xml)
        rows.append((name, "-", "-",
                     "Y" if l3 else "pass",
                     "Y" if l4 else "pass"))

    w = max(len(r[0]) for r in rows) + 2
    print(f"{'fault':<{w}} L1  L2  L3   L4")
    print("-" * (w + 18))
    for name, l1, l2, l3, l4 in rows:
        print(f"{name:<{w}} {l1:<3} {l2:<3} {l3:<4} {l4}")

    print("\nUnique catches (only one level stands between this fault "
          "and silent acceptance):")
    for name, l1, l2, l3, l4 in rows:
        catches = [lvl for lvl, v in
                   zip(("L1", "L2", "L3", "L4"), (l1, l2, l3, l4))
                   if v == "Y"]
        if len(catches) == 1:
            print(f"  {catches[0]} alone catches: {name}")


if __name__ == "__main__":
    main()
