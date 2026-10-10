# Web3D 2026 AI & Web3D Innovation Competition — submission kit

Submission page: https://web3d.siggraph.org/2026/ai-web3d-innovation-competition/  
Deadline: September 30, 2026  
Studio URL: https://x3dmcp.vercel.app  
Source: https://github.com/Web3DConsortium/x3d_mcp (ensure the Studio changes are merged or link the exact public feature branch)

## Technical overview

**x3d_mcp Studio** is a browser-facing demonstration of an open-standard 3D authoring toolchain. The Next.js/React interface offers guided geometry controls, a live X_ITE X3D preview, scene XML export, and an inspector. A server-side Next.js route establishes a Model Context Protocol (MCP) Streamable HTTP session with the separately deployed Python `x3d_mcp` server. The geometry action calls `create_geometry`; the Inspector calls `validate_x3d` against the bundled X3D 4.1 XSD and `validate_semantic` for authoring issues. Browser-local XML and scene metrics are shown separately from those backend results. The MCP server remains reusable by other clients, including AI assistants.

**Architecture:** browser (React + X_ITE) → Next.js API bridge (Vercel) → Streamable HTTP `/mcp` → Python/FastMCP tools (Render). The browser does not need direct access to MCP session IDs or cross-origin access to Render. The sample scene works without the backend; generation and MCP validation require it.

**AI model used in Studio:** none. Studio is a guided, direct-tool client and does not currently run an LLM or provide natural-language chat. The AI integration of the overall project is the model-agnostic MCP interface: compatible AI clients can discover and invoke the same X3D generation, inspection, conversion, and validation tools. The planned video demonstrates this with ChatGPT as the MCP client; add the exact model name only if it is verifiable in the recording. Do not represent Studio's guided controls as AI-generated content.

**Web3D framework and standards:** X3D 4.1 scene documents, X_ITE for browser rendering, X3DUOM-backed tool metadata, XSD validation, and additional semantic authoring checks. The server supports additional X3D workflows and encodings beyond the narrow Studio geometry demo; the video should distinguish server capabilities from features exposed in Studio.

## Innovation statement (under 500 words)

Most AI-assisted 3D demos stop at a picture or a proprietary scene graph. x3d_mcp takes a different route: it gives AI assistants an interoperable tool interface to create and reason about X3D, the open standard for interactive 3D on the Web. The resulting scene is not a hidden artifact. It is a portable document that can be rendered, inspected, validated, edited, and reused by other X3D tools.

The project joins three layers that are often separate. First, the Python MCP server exposes high-level and granular X3D authoring tools to compatible AI clients. Second, its schema and semantic checks catch problems that can otherwise survive generation and fail only when a scene is rendered or reused. Third, Studio makes the workflow visible in a browser: a judge can create geometry through MCP, orbit the live X_ITE preview, read or export the X3D source, and see actual validation findings. The interface labels local checks and server validation separately so users can tell what has been verified.

The central innovation is standards-grounded AI authoring rather than one-off 3D generation. MCP keeps the AI client replaceable; X3D keeps the artifact portable; validation makes the output accountable. This combination can support education, scientific visualization, accessibility, digital heritage, and collaborative 3D publishing without tying content to a single model or rendering platform.

The current Studio demo uses guided controls, not an embedded language model. AI-assisted creation is demonstrated through a separate MCP-compatible client connected to the same server. This separation is intentional: the browser experience showcases transparent rendering and verification, while the MCP interface allows AI clients to evolve independently.

## Four-minute video outline

1. **0:00–0:30 — Problem and claim.** Show the public Studio URL. Explain that AI-generated 3D needs an open, inspectable, valid artifact, not just a visual result.
2. **0:30–1:20 — Browser proof.** Start with the curated scene; orbit it. Choose a different shape/color/scale and click **Create with MCP**. Say that this is a direct MCP tool call, not a chat prompt.
3. **1:20–2:00 — Trust and portability.** Show the Inspector's XSD and semantic results, open Scene XML, and export the `.x3d`. Mention that the server uses X3D 4.1 validation and semantic checks.
4. **2:00–3:15 — Actual AI proof.** In ChatGPT with x3d_mcp connected through MCP, ask it to create or inspect an X3D scene. Show the actual tool invocation and output. Name the specific model only if the interface confirms it. Do **not** narrate a simulated prompt as AI behavior.
5. **3:15–4:00 — Architecture and impact.** Briefly show browser → Vercel bridge → Render MCP backend, then return to the rendered scene. Close on reusable, standards-compliant X3D and model-agnostic AI integration.

Record the browser and the AI-client proof while both are working. A Render free-tier cold start may delay the first call, so warm the backend before recording and preserve an honest continuous demonstration of the important action.

## Final submission check

- [ ] Public Studio URL works on a fresh browser session and **Create with MCP** plus validation complete.
- [ ] GitHub URL resolves to source containing the current Studio implementation (merge the PR or link a public feature branch/commit).
- [ ] Technical overview identifies ChatGPT as the MCP client and, if visible, the actual model used in the recording.
- [ ] Required 3–5 minute video is recorded, hosted, and accessible to judges.
- [ ] Innovation statement is pasted (and remains below 500 words).
- [ ] EasyChair entry is submitted before September 30, 2026; confirm the competition track/category and retain the confirmation.
