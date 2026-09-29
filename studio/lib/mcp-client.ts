const DEFAULT_PROTOCOL_VERSION = "2025-11-25";
const DEFAULT_REQUEST_TIMEOUT_MS = 60_000;

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

export type ValidationResult = {
  schema: { valid: boolean; errors: string[] };
  semantic: {
    errors: string[];
    warnings: string[];
    infoCount: number;
  };
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
    const detail = body.trim().slice(0, 500);
    throw new Error(
      `MCP server returned HTTP ${response.status}${detail ? `: ${detail}` : "."}`,
    );
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
  const configuredTimeout = Number(process.env.MCP_REQUEST_TIMEOUT_MS);
  const timeoutMs = Number.isFinite(configuredTimeout) && configuredTimeout > 0
    ? configuredTimeout
    : DEFAULT_REQUEST_TIMEOUT_MS;
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
    signal: AbortSignal.timeout(timeoutMs),
  });

  return {
    message: await readResponse<T>(response),
    sessionId: response.headers.get("mcp-session-id") || sessionId,
  };
}

function extractToolText(result: ToolCallResult, tool: string): string {
  const text = result.content?.find(
    (item): item is McpTextContent => item.type === "text" && "text" in item,
  )?.text;

  if (!text) throw new Error(`${tool} returned no text content.`);
  if (result.isError) throw new Error(text);
  return text;
}

function extractX3d(result: ToolCallResult): string {
  const text = extractToolText(result, "create_geometry");

  const document = text.match(/(?:<\?xml[\s\S]*?)?<X3D\b[\s\S]*?<\/X3D>/i)?.[0];
  if (!document) throw new Error("create_geometry returned text, but no X3D document was found.");
  return document;
}

type McpSession = {
  callTool: (name: string, args: Record<string, unknown>) => Promise<ToolCallResult>;
};

async function withMcpSession<T>(endpoint: string, action: (session: McpSession) => Promise<T>): Promise<T> {
  const protocolVersion = process.env.MCP_PROTOCOL_VERSION || DEFAULT_PROTOCOL_VERSION;
  let activeProtocolVersion = protocolVersion;
  let sessionId: string | undefined;
  let nextId = 2;

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
    activeProtocolVersion = negotiatedVersion;
    await mcpPost(
      endpoint,
      { jsonrpc: "2.0", method: "notifications/initialized" },
      negotiatedVersion,
      sessionId,
    );

    return await action({
      async callTool(name, args) {
        const called = await mcpPost<ToolCallResult>(
          endpoint,
          {
            jsonrpc: "2.0",
            id: nextId++,
            method: "tools/call",
            params: { name, arguments: args },
          },
          negotiatedVersion,
          sessionId,
        );
        if (!called.message?.result) throw new Error(`${name} returned no result.`);
        return called.message.result;
      },
    });
  } finally {
    if (sessionId) {
      const headers = new Headers({
        Accept: "application/json, text/event-stream",
        "MCP-Protocol-Version": activeProtocolVersion,
        "Mcp-Session-Id": sessionId,
      });
      void fetch(endpoint, { method: "DELETE", headers }).catch(() => undefined);
    }
  }
}

export async function createGeometryViaMcp(endpoint: string, args: GeometryArguments): Promise<string> {
  return withMcpSession(endpoint, async ({ callTool }) =>
    extractX3d(await callTool("create_geometry", { ...args, encoding: "xml" })),
  );
}

function parseSchema(result: ToolCallResult): ValidationResult["schema"] {
  const parsed: unknown = JSON.parse(extractToolText(result, "validate_x3d"));
  if (!parsed || typeof parsed !== "object") throw new Error("validate_x3d returned an invalid report.");
  const report = parsed as Record<string, unknown>;
  if (typeof report.valid !== "boolean" || !Array.isArray(report.errors) ||
      !report.errors.every((error) => typeof error === "string")) {
    throw new Error("validate_x3d returned an invalid report.");
  }
  return { valid: report.valid, errors: report.errors as string[] };
}

function parseSemantic(result: ToolCallResult): ValidationResult["semantic"] {
  const text = extractToolText(result, "validate_semantic");
  if (text.startsWith("# Semantic Check: All Clear")) {
    return { errors: [], warnings: [], infoCount: 0 };
  }
  if (text.startsWith("# Semantic Check: Parse Error") ||
      text.startsWith("# Semantic Check: No Scene") ||
      text.startsWith("# Semantic Check: Input Error")) {
    return { errors: [text.split("\n\n").slice(1).join("\n\n").trim() || text], warnings: [], infoCount: 0 };
  }
  const counts = text.match(/Found (\d+) error\(s\), (\d+) warning\(s\), (\d+) info\(s\)\./);
  if (!text.startsWith("# Semantic Check Report") || !counts) {
    throw new Error("validate_semantic returned an unrecognized report.");
  }
  const section = (name: string) =>
    text.match(new RegExp(`## ${name}\\n\\n([\\s\\S]*?)(?=\\n## |$)`))?.[1]
      .split("\n")
      .filter((line) => line.startsWith("- "))
      .map((line) => line.replace(/^- \*\*\[[^\]]+\]\*\* /, "")) || [];
  const errors = section("Errors");
  const warnings = section("Warnings");
  if (errors.length !== Number(counts[1]) || warnings.length !== Number(counts[2])) {
    throw new Error("validate_semantic returned an incomplete report.");
  }
  return { errors, warnings, infoCount: Number(counts[3]) };
}

export async function validateSceneViaMcp(endpoint: string, content: string): Promise<ValidationResult> {
  return withMcpSession(endpoint, async ({ callTool }) => {
    const schema = parseSchema(await callTool("validate_x3d", { content, encoding: "xml" }));
    const semantic = parseSemantic(await callTool("validate_semantic", { content }));
    return { schema, semantic };
  });
}
