# x3d_mcp Studio

Competition-facing browser UI for the existing `x3d_mcp` server. The Studio is a separate Next.js client: it renders X3D with X_ITE and talks to the Python backend through a small server-side MCP bridge.

## Run locally

Start the existing MCP server from the repository root:

```bash
MCP_TRANSPORT=streamable-http PORT=8000 .venv/bin/python src/server.py
```

Then start Studio in a second terminal:

```bash
cd studio
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. The curated sample works immediately. **Create with MCP** performs a real `initialize` → `tools/call(create_geometry)` round trip through the configured `/mcp` endpoint and replaces the live preview with the returned X3D.

## Architecture

```text
Browser (React + X_ITE)
        │ POST /api/mcp/create-geometry
        ▼
Next.js server route (MCP session bridge)
        │ Streamable HTTP /mcp
        ▼
Existing x3d_mcp Python server
```

`MCP_SERVER_URL` is server-only, so browser clients never receive backend session IDs or need direct CORS access. The local inspector intentionally labels its current checks as local XML/scene checks; `validate_x3d` and `validate_semantic` are represented as the next MCP pipeline hook rather than simulated results.

For Vercel, set `MCP_SERVER_URL` for both Preview and Production to the public
Render service URL. A bare service URL is normalized to `/mcp`; any other path is
rejected with a clear configuration error. `MCP_REQUEST_TIMEOUT_MS` defaults to
60 seconds so a sleeping Render free instance has time to cold-start.

## Next integration points

- Add `validate_x3d` and `validate_semantic` calls after generation.
- Add MCP tool event streaming to the activity trace.
- Add LLM orchestration only after direct tool calls remain reliable.
- Persist scene revisions in a session-scoped workspace.
