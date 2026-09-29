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

Open `http://localhost:3000`. The curated sample works immediately. **Create with MCP** performs a real `initialize` → `tools/call(create_geometry)` round trip through the configured `/mcp` endpoint and replaces the live preview with the returned X3D. Studio also calls `validate_x3d` and `validate_semantic` for the sample and each generated scene, showing XSD errors and semantic warnings in the Inspector. Use **Retry** if a sleeping backend times out.

## Architecture

```text
Browser (React + X_ITE)
        │ POST /api/mcp/create-geometry or /api/mcp/validate-scene
        ▼
Next.js server route (MCP session bridge)
        │ Streamable HTTP /mcp
        ▼
Existing x3d_mcp Python server
```

`MCP_SERVER_URL` is server-only, so browser clients never receive backend session IDs or need direct CORS access. The local document checks and the remote MCP validation results are labeled separately. The status indicator reports the latest validation connection result; it does not claim the backend is healthy before a request succeeds.

For Vercel, set `MCP_SERVER_URL` for both Preview and Production to the public
Render service URL. A bare service URL is normalized to `/mcp`; any other path is
rejected with a clear configuration error. `MCP_REQUEST_TIMEOUT_MS` defaults to
60 seconds so a sleeping Render free instance has time to cold-start.

## Current scope and next integration points

- The left panel is guided tool control, not LLM chat. AI clients can connect to the same MCP backend separately; Studio does not embed an AI model or require an API key.
- Add MCP tool event streaming to the activity trace.
- Add LLM orchestration only after direct tool calls remain reliable.
- Persist scene revisions in a session-scoped workspace.
