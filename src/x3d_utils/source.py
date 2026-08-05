"""Resolve X3D input from either inline content or a filesystem path.

Generated X3D scenes are routinely hundreds of KB -- forcing the model to inline
the whole document just to validate or render it is wasteful and error-prone.
Every tool that consumes a scene should accept a `path` as an alternative to
`content`; this is the single shared resolver they call.
"""

import os
from pathlib import Path


def _http_transport_active() -> bool:
    """Whether the server is running over the Streamable HTTP transport.

    Path input is a local-use affordance; over HTTP it would let remote
    callers read files from the server's filesystem (same policy as
    tools.scene_ops).
    """
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    return transport in ("http", "streamable-http")


def load_x3d_source(content: str | None = None, path: str | None = None) -> str:
    """Return X3D text from exactly one of `content` (inline) or `path` (a file).

    Raises ValueError if neither or both are given, or if the file is missing --
    callers should surface the message to the user.
    """
    has_content = content is not None and content.strip() != ""
    has_path = path is not None and path.strip() != ""

    if has_path and has_content:
        raise ValueError(
            "Provide either `content` (inline X3D) or `path` (a file), not both."
        )
    if not has_path and not has_content:
        raise ValueError("Provide either `content` (inline X3D) or `path` (a file).")

    if has_path:
        if _http_transport_active():
            raise ValueError(
                "Path input is disabled over the HTTP transport. "
                "Provide inline X3D content instead."
            )
        p = Path(path).expanduser()
        if not p.is_file():
            raise ValueError(f"X3D file not found: {p}")
        try:
            return p.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Could not read X3D file {p}: {exc}") from exc

    return content
