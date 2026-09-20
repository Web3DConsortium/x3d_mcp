import { NextResponse } from "next/server";
import {
  createGeometryViaMcp,
  type GeometryArguments,
} from "@/lib/mcp-client";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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
    const endpoint = process.env.MCP_SERVER_URL || "http://127.0.0.1:8000/mcp";
    const x3d = await createGeometryViaMcp(endpoint, args);

    return NextResponse.json({
      x3d,
      tool: "create_geometry",
      durationMs: Math.round(performance.now() - startedAt),
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unknown MCP error";
    const connectionFailure =
      detail.includes("fetch failed") ||
      detail.includes("ECONNREFUSED") ||
      detail.includes("aborted");

    return NextResponse.json(
      {
        error: connectionFailure
          ? "The MCP backend is not reachable. Start x3d_mcp in Streamable HTTP mode and try again."
          : detail,
      },
      { status: connectionFailure ? 503 : 502 },
    );
  }
}
