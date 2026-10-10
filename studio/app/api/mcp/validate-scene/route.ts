import { NextResponse } from "next/server";
import { mcpEndpoint } from "@/lib/mcp-endpoint";
import { validateSceneViaMcp } from "@/lib/mcp-client";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

export async function POST(request: Request) {
  try {
    const body: unknown = await request.json();
    const content = body && typeof body === "object" && "content" in body
      ? (body as { content: unknown }).content
      : undefined;
    if (typeof content !== "string" || !content.trim() || content.length > 1_000_000) {
      return NextResponse.json({ error: "Provide an X3D document under 1 MB." }, { status: 400 });
    }
    const validation = await validateSceneViaMcp(mcpEndpoint(), content);
    return NextResponse.json(validation);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unknown MCP error";
    const normalized = detail.toLowerCase();
    const timedOut = normalized.includes("timeout") || normalized.includes("timed out") || normalized.includes("aborted");
    const connectionFailure = timedOut || normalized.includes("fetch failed") || normalized.includes("econnrefused");
    console.error("[validate-scene] MCP request failed", { error: detail, configured: Boolean(process.env.MCP_SERVER_URL) });
    return NextResponse.json({
      error: timedOut
        ? "The MCP backend took too long to wake up. Wait a moment and retry validation."
        : connectionFailure
          ? "The MCP backend is not reachable. Confirm the Render service is running."
          : detail,
    }, { status: timedOut ? 504 : connectionFailure || normalized.includes("mcp_server_url") ? 503 : 502 });
  }
}
