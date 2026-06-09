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

_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio").lower()
_IS_HTTP = _TRANSPORT in ("http", "streamable-http")

_real_stdout = sys.stdout
sys.stdout = sys.stderr
from tools import (
    workflow, granular, convert, query, validate_tool, render, scene_ops, animate,
    prompts,
)
sys.stdout = _real_stdout

_fastmcp_kwargs = {}
if _IS_HTTP:
    _fastmcp_kwargs["host"] = os.environ.get("HOST", "0.0.0.0")
    _fastmcp_kwargs["port"] = int(os.environ.get("PORT", "8000"))

mcp = FastMCP("x3d-mcp", **_fastmcp_kwargs)

workflow.register(mcp)
granular.register(mcp)
convert.register(mcp)
query.register(mcp)
validate_tool.register(mcp)
render.register(mcp)
scene_ops.register(mcp)
animate.register(mcp)
prompts.register(mcp)


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
