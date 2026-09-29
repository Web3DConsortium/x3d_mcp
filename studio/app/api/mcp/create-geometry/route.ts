import { NextResponse } from "next/server";
import {
  createGeometryViaMcp,
  type GeometryArguments,
} from "@/lib/mcp-client";
import { mcpEndpoint } from "@/lib/mcp-endpoint";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const SHAPES = new Set(["box", "sphere", "cone", "cylinder"]);

function finiteNumbers(value: unknown, length?: number): value is number[] {
  return (
    Array.isArray(value) &&
    (length === undefined || value.length === length) &&
    value.every((item) => typeof item === "number" && Number.isFinite(item))
  );
}

function readArguments(value: unknown): GeometryArguments {
  if (!value || typeof value !== "object") throw new Error("Request body must be an object.");
  const input = value as Record<string, unknown>;

  if (typeof input.shape !== "string" || !SHAPES.has(input.shape)) {
    throw new Error("shape must be box, sphere, cone, or cylinder.");
  }
  if (!finiteNumbers(input.color, 3) || input.color.some((part) => part < 0 || part > 1)) {
    throw new Error("color must contain three values between 0 and 1.");
  }
  if (input.size !== undefined && !finiteNumbers(input.size)) {
    throw new Error("size must be a list of numbers.");
  }

  return {
    shape: input.shape as GeometryArguments["shape"],
    color: input.color as [number, number, number],
    size: input.size as number[] | undefined,
  };
}

export async function POST(request: Request) {
  const startedAt = performance.now();

  try {
    const args = readArguments(await request.json());
    const endpoint = mcpEndpoint();
    const x3d = await createGeometryViaMcp(endpoint, args);

    return NextResponse.json({
      x3d,
      tool: "create_geometry",
      durationMs: Math.round(performance.now() - startedAt),
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unknown MCP error";
    const normalizedDetail = detail.toLowerCase();
    const timedOut =
      normalizedDetail.includes("timeout") ||
      normalizedDetail.includes("timed out") ||
      normalizedDetail.includes("aborted");
    const connectionFailure =
      timedOut ||
      normalizedDetail.includes("fetch failed") ||
      normalizedDetail.includes("econnrefused");
    const configurationFailure = normalizedDetail.includes("mcp_server_url");

    console.error("[create-geometry] MCP request failed", {
      error: detail,
      configured: Boolean(process.env.MCP_SERVER_URL),
    });

    return NextResponse.json(
      {
        error: timedOut
          ? "The MCP backend took too long to wake up. Render free services can cold-start; wait a moment and try again."
          : connectionFailure
            ? "The MCP backend is not reachable. Confirm the Render service is running in Streamable HTTP mode."
            : detail,
      },
      { status: timedOut ? 504 : connectionFailure || configurationFailure ? 503 : 502 },
    );
  }
}
