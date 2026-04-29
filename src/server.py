"""X3D MCP Server.

FastMCP server providing tools for generating, validating, and converting
valid X3D 4.1 content.
"""

import sys
from pathlib import Path

# Ensure src is on the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from tools import (
    workflow, granular, convert, query, validate_tool, render, scene_ops, animate,
)

mcp = FastMCP("x3d-mcp")

workflow.register(mcp)
granular.register(mcp)
convert.register(mcp)
query.register(mcp)
validate_tool.register(mcp)
render.register(mcp)
scene_ops.register(mcp)
animate.register(mcp)


if __name__ == "__main__":
    mcp.run()
