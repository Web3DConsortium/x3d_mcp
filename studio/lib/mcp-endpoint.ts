export function mcpEndpoint(): string {
  const configured = process.env.MCP_SERVER_URL?.trim();

  if (!configured) {
    if (process.env.NODE_ENV === "production") {
      throw new Error(
        "MCP_SERVER_URL is not configured for this deployment. Add the Render service URL in Vercel and redeploy.",
      );
    }
    return "http://127.0.0.1:8000/mcp";
  }

  let endpoint: URL;
  try {
    endpoint = new URL(configured);
  } catch {
    throw new Error("MCP_SERVER_URL must be a valid absolute URL.");
  }

  const path = endpoint.pathname.replace(/\/+$/, "");
  if (!path) {
    endpoint.pathname = "/mcp";
  } else if (path !== "/mcp") {
    throw new Error("MCP_SERVER_URL must point to the backend's /mcp endpoint.");
  } else {
    endpoint.pathname = path;
  }

  return endpoint.toString();
}
