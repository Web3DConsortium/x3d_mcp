"""X3D MCP Server.

FastMCP server providing tools for generating, validating, and converting
valid X3D 4.1 content.

Transport is selected by the MCP_TRANSPORT environment variable:
  - "stdio" (default): launched as a subprocess by a desktop MCP client.
  - "streamable-http" (or "http"): listens for remote MCP clients over
    HTTP. Host and port come from HOST and PORT (PORT is injected by
    hosts like Render). Endpoint path is /mcp.
"""

import os
import sys
from pathlib import Path

# Ensure src is on the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio").lower()
_IS_HTTP = _TRANSPORT in ("http", "streamable-http")

_real_stdout = sys.stdout
sys.stdout = sys.stderr
from tools import (
    workflow, granular, convert, query, validate_tool, render, scene_ops, animate,
    prompts, semantics,
)
sys.stdout = _real_stdout

# Surfaced to the client on connect -- the proactive "read me first" that keeps a
# fresh model on X3D's canonical path instead of improvising from the flat node list.
INSTRUCTIONS = """\
X3D is authored ONE canonical way. Follow the path below every time; do not improvise \
field names, containerFields, or node placement from memory -- this server is the ground truth.

THE PATH
1. LOOK UP before you build. `describe_node('<Name>')` gives a node's exact fields, types, \
default containerField, and which child node types each field accepts. `list_nodes(component=...)` \
discovers nodes. Never guess field or containerField names.
2. BUILD (workflow tools: create_scene / create_geometry / compose_scene; or granular: \
create_node / set_field / add_child / add_route).
3. VALIDATE -- always BOTH: `validate_x3d` (XSD schema) and `validate_semantic` (the errors that \
pass the schema but still break rendering -- wrong containerField, USE-before-DEF, broken ROUTEs). \
validate_semantic names the exact fix; apply it.
4. RENDER and LOOK before declaring done: `render_image(content|path)` returns a PNG you \
inspect directly; `x3dom_page` gives an interactive browser page. A scene that validates can \
still be visually wrong (off-camera, unlit, mis-scaled).
Rule: a scene is not finished until validate_semantic is clean AND you have rendered it.

For any multi-step task, START from a prompt (build_scene, animate_scene, audit_scene, \
convert_to_x3dom). They encode the known-good tool order so you don't have to rediscover it.

NON-OBVIOUS RULES THAT CAUSE SILENT FAILURES (validate_semantic enforces all of these):
- containerField: every child node belongs to a specific *field* of its parent. A node's DEFAULT \
containerField only fits its usual parent; when you place it elsewhere you MUST set containerField \
explicitly -- e.g. a texture inside PhysicalMaterial needs baseTexture/normalTexture/..., an \
HAnimHumanoid skeleton root needs containerField='skeleton', skinCoord/skinNormal likewise. A wrong \
or defaulted containerField makes a conforming viewer silently drop or misfile the node (blank render). \
`autofix_x3d` rewrites these for you and returns the corrected document.
- DEF before USE: a USE must appear AFTER the DEF it references, in document order.
- ROUTE field types and access types must match source->target.

When unsure, the answer is describe_node + validate_semantic -- not recall."""

_fastmcp_kwargs = {}
if _IS_HTTP:
    _fastmcp_kwargs["host"] = os.environ.get("HOST", "0.0.0.0")
    _fastmcp_kwargs["port"] = int(os.environ.get("PORT", "8000"))

mcp = FastMCP("x3d-mcp", instructions=INSTRUCTIONS, **_fastmcp_kwargs)

workflow.register(mcp)
granular.register(mcp)
convert.register(mcp)
query.register(mcp)
validate_tool.register(mcp)
render.register(mcp)
scene_ops.register(mcp)
animate.register(mcp)
prompts.register(mcp)
semantics.register(mcp)


# Friendly responses on the root and /pulse paths under HTTP transport.
# These are no-ops under stdio. Without them, browser and platform hits
# to "/" return a 404 from FastMCP's app -- correct for the MCP protocol
# but unfriendly to humans and to host platforms probing for liveness.
# /pulse is intended as the configured health-check endpoint on hosts
# like Render and is kept dependency-free so it stays fast and reliable.
@mcp.custom_route("/", methods=["GET"])
async def _root(_request):
    return JSONResponse(
        {
            "name": "x3d-mcp",
            "description": "Web3D Consortium MCP server for X3D 4.0/4.1 authoring.",
            "mcp_endpoint": mcp.settings.streamable_http_path,
            "health_endpoint": "/pulse",
            "repository": "https://github.com/Web3DConsortium/x3d_mcp",
        }
    )


@mcp.custom_route("/pulse", methods=["GET"])
async def _pulse(_request):
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    if _IS_HTTP:
        print(
            f"x3d-mcp listening on http://{mcp.settings.host}:{mcp.settings.port}"
            f"{mcp.settings.streamable_http_path} (streamable-http)",
            file=sys.stderr,
        )
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
