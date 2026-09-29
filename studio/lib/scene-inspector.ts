export type SceneFacts = {
  wellFormed: boolean;
  hasX3dRoot: boolean;
  hasScene: boolean;
  profile: string;
  version: string;
  nodeCount: number;
  shapeCount: number;
  namedNodes: number;
  bytes: number;
  error?: string;
};

export function unparsedSceneFacts(source: string): SceneFacts {
  return {
    wellFormed: false,
    hasX3dRoot: false,
    hasScene: false,
    profile: "—",
    version: "—",
    nodeCount: 0,
    shapeCount: 0,
    namedNodes: 0,
    bytes: new TextEncoder().encode(source).length,
  };
}

export function inspectScene(source: string): SceneFacts {
  const base = unparsedSceneFacts(source);

  if (typeof DOMParser === "undefined") return base;

  const document = new DOMParser().parseFromString(source, "application/xml");
  const parserError = document.querySelector("parsererror");
  if (parserError) {
    return { ...base, error: parserError.textContent?.trim() || "Invalid XML" };
  }

  const root = document.documentElement;
  const scene = Array.from(root.children).find(
    (node) => node.tagName.toLowerCase() === "scene",
  );
  const allNodes = scene ? Array.from(scene.querySelectorAll("*")) : [];

  return {
    ...base,
    wellFormed: true,
    hasX3dRoot: root.tagName.toLowerCase() === "x3d",
    hasScene: Boolean(scene),
    profile: root.getAttribute("profile") || "—",
    version: root.getAttribute("version") || "—",
    nodeCount: allNodes.length,
    shapeCount: allNodes.filter((node) => node.tagName.toLowerCase() === "shape").length,
    namedNodes: allNodes.filter((node) => node.hasAttribute("DEF")).length,
  };
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}
