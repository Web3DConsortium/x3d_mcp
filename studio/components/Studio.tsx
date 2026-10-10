"use client";

import { useEffect, useState } from "react";
import { SAMPLE_SCENE } from "@/lib/sample-scene";
import {
  formatBytes,
  inspectScene,
  unparsedSceneFacts,
} from "@/lib/scene-inspector";
import { X3DViewer } from "@/components/X3DViewer";
import type { ValidationResult } from "@/lib/mcp-client";
import {
  AlertIcon,
  ChatIcon,
  CheckIcon,
  CopyIcon,
  CubeIcon,
  DownloadIcon,
  EyeIcon,
  InspectorIcon,
  RotateIcon,
  SendIcon,
  SparkIcon,
  TerminalIcon,
} from "@/components/icons";

type ShapeName = "box" | "sphere" | "cone" | "cylinder";
type SceneOrigin = {
  label: string;
  detail: string;
  durationMs?: number;
  kind: "sample" | "mcp";
};
type ValidationState =
  | { status: "checking" }
  | { status: "ready"; result: ValidationResult }
  | { status: "unavailable"; error: string };

const SHAPES: Array<{ name: ShapeName; label: string }> = [
  { name: "box", label: "Box" },
  { name: "sphere", label: "Sphere" },
  { name: "cone", label: "Cone" },
  { name: "cylinder", label: "Cylinder" },
];

const COLORS = [
  { label: "Cyan", hex: "#21c7e8", rgb: [0.13, 0.78, 0.91] },
  { label: "Violet", hex: "#8b5cf6", rgb: [0.55, 0.36, 0.96] },
  { label: "Coral", hex: "#ff7a59", rgb: [1, 0.48, 0.35] },
  { label: "Mint", hex: "#4ade9b", rgb: [0.29, 0.87, 0.61] },
] as const;

function sizeFor(shape: ShapeName, scale: number): number[] {
  if (shape === "box") return [scale, scale, scale];
  if (shape === "sphere") return [scale / 2];
  return [scale / 2, scale];
}

function PanelTitle({
  icon,
  eyebrow,
  title,
  trailing,
}: {
  icon: React.ReactNode;
  eyebrow: string;
  title: string;
  trailing?: React.ReactNode;
}) {
  return (
    <div className="panel-heading">
      <div className="panel-title-icon">{icon}</div>
      <div>
        <span>{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {trailing && <div className="panel-trailing">{trailing}</div>}
    </div>
  );
}

function StatusRow({
  label,
  detail,
  valid,
  pending,
  warning,
}: {
  label: string;
  detail: string;
  valid?: boolean;
  pending?: boolean;
  warning?: boolean;
}) {
  return (
    <div className={`status-row ${pending ? "status-pending" : warning ? "status-warning" : valid ? "" : "status-error"}`}>
      <span className="status-icon">
        {valid ? <CheckIcon /> : pending ? <span>···</span> : <AlertIcon />}
      </span>
      <span>
        <strong>{label}</strong>
        <small>{detail}</small>
      </span>
    </div>
  );
}

export function Studio() {
  const [scene, setScene] = useState(SAMPLE_SCENE);
  const [origin, setOrigin] = useState<SceneOrigin>({
    label: "Curated sample",
    detail: "Loaded locally",
    kind: "sample",
  });
  const [shape, setShape] = useState<ShapeName>("sphere");
  const [colorIndex, setColorIndex] = useState(0);
  const [scale, setScale] = useState(2.6);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string>();
  const [inspectorTab, setInspectorTab] = useState<"overview" | "source">("overview");
  const [copied, setCopied] = useState(false);
  const [validation, setValidation] = useState<ValidationState>({ status: "checking" });
  const [validationRevision, setValidationRevision] = useState(0);

  const [facts, setFacts] = useState(() => unparsedSceneFacts(SAMPLE_SCENE));
  const selectedColor = COLORS[colorIndex];

  useEffect(() => {
    setFacts(inspectScene(scene));
  }, [scene]);

  useEffect(() => {
    const controller = new AbortController();
    setValidation({ status: "checking" });
    async function validate() {
      try {
        const response = await fetch("/api/mcp/validate-scene", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: scene }),
          signal: controller.signal,
        });
        const result = await response.json() as ValidationResult & { error?: string };
        if (!response.ok) throw new Error(result.error || "The MCP validation request failed.");
        if (!controller.signal.aborted) setValidation({ status: "ready", result });
      } catch (caught) {
        if (!controller.signal.aborted) {
          setValidation({
            status: "unavailable",
            error: caught instanceof Error ? caught.message : "The MCP validation request failed.",
          });
        }
      }
    }
    void validate();
    return () => controller.abort();
  }, [scene, validationRevision]);

  const validationHasIssues = validation.status === "ready" &&
    (!validation.result.schema.valid || validation.result.semantic.errors.length > 0 ||
      validation.result.semantic.warnings.length > 0);
  const validationHasErrors = validation.status === "ready" &&
    (!validation.result.schema.valid || validation.result.semantic.errors.length > 0);
  const validationSummary = validation.status === "checking"
    ? "Running XSD + semantic checks"
    : validation.status === "unavailable"
      ? "MCP check unavailable"
      : validationHasIssues
        ? "Review findings below"
        : "XSD + semantic checks passed";

  async function createGeometry() {
    setIsGenerating(true);
    setError(undefined);
    try {
      const response = await fetch("/api/mcp/create-geometry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          shape,
          color: selectedColor.rgb,
          size: sizeFor(shape, scale),
        }),
      });
      const result = (await response.json()) as {
        x3d?: string;
        tool?: string;
        durationMs?: number;
        error?: string;
      };
      if (!response.ok || !result.x3d) {
        throw new Error(result.error || "create_geometry did not return a scene.");
      }
      setScene(result.x3d);
      setOrigin({
        label: "MCP generated",
        detail: `${result.tool} · ${shape}`,
        durationMs: result.durationMs,
        kind: "mcp",
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The MCP request failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  function restoreSample() {
    setScene(SAMPLE_SCENE);
    setOrigin({ label: "Curated sample", detail: "Loaded locally", kind: "sample" });
    setError(undefined);
  }

  function downloadScene() {
    const url = URL.createObjectURL(new Blob([scene], { type: "model/x3d+xml" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = origin.kind === "mcp" ? `mcp-${shape}.x3d` : "studio-observatory.x3d";
    link.click();
    URL.revokeObjectURL(url);
  }

  async function copyScene() {
    await navigator.clipboard.writeText(scene);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="studio-shell">
      <header className="topbar">
        <a className="brand" href="https://github.com/Web3DConsortium/x3d_mcp" target="_blank" rel="noreferrer">
          <span className="brand-mark"><CubeIcon /></span>
          <span>
            <strong>x3d<span>_mcp</span></strong>
            <small>Studio</small>
          </span>
        </a>
        <div className="topbar-center">
          <span className="competition-pill"><SparkIcon /> AI × Web3D 2026</span>
          <span className="topbar-copy">Open standards. Intelligent creation.</span>
        </div>
        <div className={`server-status ${validation.status}`} title="Status of the latest MCP validation request">
          <span className="status-dot" />
          {validation.status === "ready" ? "MCP connected" : validation.status === "checking" ? "Checking MCP…" : "MCP unavailable"}
        </div>
      </header>

      <main className="workspace">
        <section className="panel chat-panel">
          <PanelTitle
            icon={<ChatIcon />}
            eyebrow="Create"
            title="Studio Assistant"
            trailing={<span className="preview-label">Preview</span>}
          />

          <div className="chat-scroll">
            <div className="chat-intro">
              <span><SparkIcon /></span>
              <h3>Build the open 3D web</h3>
              <p>Turn ideas into standards-compliant X3D scenes through inspectable tools.</p>
            </div>

            <div className="message assistant-message">
              <span className="assistant-avatar"><CubeIcon /></span>
              <div>
                <strong>Guided creation mode</strong>
                <p>Choose a shape below to call <code>create_geometry</code>. Natural-language chat is not enabled in this demo.</p>
              </div>
            </div>

            <div className="tool-composer">
              <div className="composer-label">
                <span>Direct tool control</span>
                <code>create_geometry</code>
              </div>

              <fieldset>
                <legend>Geometry</legend>
                <div className="shape-grid">
                  {SHAPES.map((option) => (
                    <button
                      type="button"
                      key={option.name}
                      className={shape === option.name ? "selected" : ""}
                      onClick={() => setShape(option.name)}
                    >
                      <span className={`shape-glyph shape-${option.name}`} />
                      {option.label}
                    </button>
                  ))}
                </div>
              </fieldset>

              <div className="control-row">
                <fieldset>
                  <legend>Material</legend>
                  <div className="swatches">
                    {COLORS.map((color, index) => (
                      <button
                        type="button"
                        key={color.label}
                        className={colorIndex === index ? "active" : ""}
                        style={{ "--swatch": color.hex } as React.CSSProperties}
                        onClick={() => setColorIndex(index)}
                        aria-label={`${color.label} material`}
                        title={color.label}
                      />
                    ))}
                  </div>
                </fieldset>
                <fieldset className="scale-control">
                  <legend>Scale <span>{scale.toFixed(1)}</span></legend>
                  <input
                    aria-label="Geometry scale"
                    type="range"
                    min="1"
                    max="4"
                    step="0.1"
                    value={scale}
                    onChange={(event) => setScale(Number(event.target.value))}
                  />
                </fieldset>
              </div>

              <button className="generate-button" type="button" onClick={createGeometry} disabled={isGenerating}>
                {isGenerating ? <span className="spinner" /> : <SendIcon />}
                {isGenerating ? "Calling x3d_mcp…" : "Create with MCP"}
              </button>
            </div>

            {error && (
              <div className="error-card" role="alert">
                <AlertIcon />
                <div><strong>Backend unavailable</strong><span>{error}</span></div>
              </div>
            )}
          </div>

          <div className="chat-footer">
            <TerminalIcon />
            <span>Next hook</span>
            <p>Natural language → tool planning</p>
          </div>
        </section>

        <section className="panel preview-panel">
          <PanelTitle
            icon={<EyeIcon />}
            eyebrow="Explore"
            title="Live 3D Preview"
            trailing={<span className="live-badge"><span /> X_ITE live</span>}
          />

          <div className="viewer-stage">
            <div className="stage-glow stage-glow-one" />
            <div className="stage-glow stage-glow-two" />
            <X3DViewer source={scene} />
            <div className="viewer-toolbar">
              <button type="button" onClick={restoreSample} disabled={origin.kind === "sample"} title="Restore sample scene">
                <RotateIcon /> Reset
              </button>
              <button type="button" onClick={downloadScene} title="Download the current X3D document">
                <DownloadIcon /> Export
              </button>
            </div>
            <div className="viewer-hint">
              <span className="mouse-icon" />
              Drag to orbit · Scroll to zoom
            </div>
          </div>

          <div className="scene-strip">
            <div className={`origin-mark ${origin.kind}`}><CubeIcon /></div>
            <div>
              <span>Current scene</span>
              <strong>{origin.label}</strong>
            </div>
            <div className="scene-provenance">
              <span>{origin.detail}</span>
              {origin.durationMs !== undefined && <small>{origin.durationMs} ms</small>}
            </div>
          </div>
        </section>

        <section className="panel inspector-panel">
          <PanelTitle
            icon={<InspectorIcon />}
            eyebrow="Understand"
            title="Inspector"
          />

          <div className="tabs" role="tablist" aria-label="Inspector views">
            <button
              type="button"
              role="tab"
              aria-selected={inspectorTab === "overview"}
              className={inspectorTab === "overview" ? "active" : ""}
              onClick={() => setInspectorTab("overview")}
            >Overview</button>
            <button
              type="button"
              role="tab"
              aria-selected={inspectorTab === "source"}
              className={inspectorTab === "source" ? "active" : ""}
              onClick={() => setInspectorTab("source")}
            >Scene XML</button>
          </div>

          {inspectorTab === "overview" ? (
            <div className="inspector-scroll">
              <div className="section-label"><span>Document health</span><small>Local checks</small></div>
              <div className="status-list">
                <StatusRow label="Well-formed XML" detail="Parsed without errors" valid={facts.wellFormed} />
                <StatusRow label="X3D document" detail={`${facts.profile} profile · version ${facts.version}`} valid={facts.hasX3dRoot} />
                <StatusRow label="Scene graph" detail={`${facts.nodeCount} nodes discovered`} valid={facts.hasScene} />
              </div>

              <div className="section-label"><span>Scene metrics</span></div>
              <div className="metric-grid">
                <div><strong>{facts.shapeCount}</strong><span>Shapes</span></div>
                <div><strong>{facts.nodeCount}</strong><span>Nodes</span></div>
                <div><strong>{facts.namedNodes}</strong><span>DEF names</span></div>
                <div><strong>{formatBytes(facts.bytes)}</strong><span>Document</span></div>
              </div>

              <div className="section-label"><span>Validation pipeline</span><small>Live MCP tools</small></div>
              <div className="pipeline-card">
                <div className="pipeline-step complete"><span>1</span><p><strong>Generate</strong><small>{origin.kind === "mcp" ? "MCP tool response" : "Sample document"}</small></p></div>
                <div className="pipeline-line active" />
                <div className="pipeline-step complete"><span>2</span><p><strong>Inspect</strong><small>Browser scene analysis</small></p></div>
                <div className={`pipeline-line ${validation.status === "ready" ? "active" : ""}`} />
                <div className={`pipeline-step ${validation.status === "checking" ? "checking" : validation.status === "unavailable" || validationHasErrors ? "issue" : validationHasIssues ? "warning" : "complete"}`}>
                  <span>3</span><p><strong>Validate</strong><small>{validationSummary}</small></p>
                </div>
              </div>

              <div className="section-label">
                <span>MCP validation</span>
                <button className="retry-button" type="button" onClick={() => setValidationRevision((value) => value + 1)} disabled={validation.status === "checking"}>Retry</button>
              </div>
              {validation.status === "checking" ? (
                <div className="validation-notice" role="status">Checking X3D 4.1 schema and scene semantics… Render may need time to wake up.</div>
              ) : validation.status === "unavailable" ? (
                <div className="validation-notice issue" role="alert">{validation.error}</div>
              ) : (
                <div className="status-list">
                  <StatusRow label="X3D 4.1 schema" detail={validation.result.schema.valid ? "No XSD errors" : `${validation.result.schema.errors.length} XSD error(s)`} valid={validation.result.schema.valid} />
                  <StatusRow label="Scene semantics" detail={`${validation.result.semantic.errors.length} errors · ${validation.result.semantic.warnings.length} warnings · ${validation.result.semantic.infoCount} notes`} valid={validation.result.semantic.errors.length === 0 && validation.result.semantic.warnings.length === 0} warning={validation.result.semantic.errors.length === 0 && validation.result.semantic.warnings.length > 0} />
                </div>
              )}
              {validation.status === "ready" && (
                <div className="validation-findings">
                  {[...validation.result.schema.errors, ...validation.result.semantic.errors].map((issue, index) => <p className="error" key={`error-${index}`}>{issue}</p>)}
                  {validation.result.semantic.warnings.map((issue, index) => <p className="warning" key={`warning-${index}`}>{issue}</p>)}
                </div>
              )}

              <div className="standard-card">
                <div className="standard-icon"><CubeIcon /></div>
                <div><span>Built on an open standard</span><strong>X3D {facts.version}</strong><small>ISO/IEC 19775 · Web3D Consortium</small></div>
              </div>
            </div>
          ) : (
            <div className="source-view">
              <div className="source-toolbar">
                <span>scene.x3d</span>
                <button type="button" onClick={copyScene}><CopyIcon /> {copied ? "Copied" : "Copy"}</button>
              </div>
              <pre><code>{scene}</code></pre>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
