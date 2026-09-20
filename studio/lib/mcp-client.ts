const DEFAULT_PROTOCOL_VERSION = "2025-11-25";

type JsonRpcResponse<T> = {
  jsonrpc: "2.0";
  id?: number;
  result?: T;
  error?: { code: number; message: string; data?: unknown };
};

type McpTextContent = { type: "text"; text: string };
type ToolCallResult = {
  content?: Array<McpTextContent | { type: string }>;
  structuredContent?: Record<string, unknown>;
  isError?: boolean;
};

export type GeometryArguments = {
  shape: "box" | "sphere" | "cone" | "cylinder";
  color: [number, number, number];
  size?: number[];
  translation?: [number, number, number];
  rotation?: [number, number, number, number];
  transparency?: number;
};

function parseSsePayload(body: string): JsonRpcResponse<unknown> {
  const dataLines = body
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim())
    .filter(Boolean);

  for (const line of dataLines) {
    try {
      return JSON.parse(line) as JsonRpcResponse<unknown>;
    } catch {
      // A stream may include keepalives or non-JSON events before the response.
    }
  }
  throw new Error("The MCP server returned an unreadable event stream.");
}

async function readResponse<T>(response: Response): Promise<JsonRpcResponse<T> | undefined> {
  if (response.status === 202 || response.status === 204) return undefined;

  const body = await response.text();
  if (!response.ok) {
    throw new Error(body || `MCP request failed with HTTP ${response.status}.`);
  }
  if (!body.trim()) return undefined;

  const contentType = response.headers.get("content-type") || "";
  const message = contentType.includes("text/event-stream")
    ? parseSsePayload(body)
    : (JSON.parse(body) as JsonRpcResponse<T>);

  if (message.error) throw new Error(message.error.message);
  return message as JsonRpcResponse<T>;
}

async function mcpPost<T>(
  endpoint: string,
  message: Record<string, unknown>,
  protocolVersion: string,
  sessionId?: string,
): Promise<{ message?: JsonRpcResponse<T>; sessionId?: string }> {
  const headers = new Headers({
    Accept: "application/json, text/event-stream",
    "Content-Type": "application/json",
    "MCP-Protocol-Version": protocolVersion,
  });
  if (sessionId) headers.set("Mcp-Session-Id", sessionId);

  const response = await fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify(message),
    cache: "no-store",
    signal: AbortSignal.timeout(15_000),
  });

  return {
    message: await readResponse<T>(response),
    sessionId: response.headers.get("mcp-session-id") || sessionId,
  };
}

function extractX3d(result: ToolCallResult): string {
  const text = result.content?.find(
    (item): item is McpTextContent => item.type === "text" && "text" in item,
  )?.text;

  if (!text) throw new Error("create_geometry returned no X3D text content.");
  if (result.isError) throw new Error(text);

  const document = text.match(/(?:<\?xml[\s\S]*?)?<X3D\b[\s\S]*?<\/X3D>/i)?.[0];
  if (!document) throw new Error("create_geometry returned text, but no X3D document was found.");
  return document;
}

export async function createGeometryViaMcp(
  endpoint: string,
  args: GeometryArguments,
): Promise<string> {
  const protocolVersion = process.env.MCP_PROTOCOL_VERSION || DEFAULT_PROTOCOL_VERSION;
  let sessionId: string | undefined;

  try {
    const initialized = await mcpPost<{
      protocolVersion: string;
      serverInfo: { name: string; version: string };
    }>(
      endpoint,
      {
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          protocolVersion,
          capabilities: {},
          clientInfo: { name: "x3d-mcp-studio", version: "0.1.0" },
        },
      },
      protocolVersion,
    );

    sessionId = initialized.sessionId;
    if (!initialized.message?.result) {
      throw new Error("The MCP server did not complete initialization.");
    }

    const negotiatedVersion = initialized.message.result.protocolVersion || protocolVersion;
    await mcpPost(
      endpoint,
      { jsonrpc: "2.0", method: "notifications/initialized" },
      negotiatedVersion,
      sessionId,
    );

    const called = await mcpPost<ToolCallResult>(
      endpoint,
      {
        jsonrpc: "2.0",
        id: 2,
        method: "tools/call",
        params: { name: "create_geometry", arguments: { ...args, encoding: "xml" } },
      },
      negotiatedVersion,
      sessionId,
    );

    if (!called.message?.result) throw new Error("The MCP tool returned no result.");
    return extractX3d(called.message.result);
  } finally {
    if (sessionId) {
      const headers = new Headers({
        Accept: "application/json, text/event-stream",
        "MCP-Protocol-Version": protocolVersion,
        "Mcp-Session-Id": sessionId,
      });
      void fetch(endpoint, { method: "DELETE", headers }).catch(() => undefined);
    }
  }
}
