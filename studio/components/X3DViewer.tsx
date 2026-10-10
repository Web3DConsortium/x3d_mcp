"use client";

import { useEffect, useState } from "react";

export function X3DViewer({ source }: { source: string }) {
  const [sceneUrl, setSceneUrl] = useState<string>();

  useEffect(() => {
    const nextUrl = URL.createObjectURL(
      new Blob([source], { type: "model/x3d+xml" }),
    );
    setSceneUrl(nextUrl);
    return () => URL.revokeObjectURL(nextUrl);
  }, [source]);

  if (!sceneUrl) {
    return <div className="viewer-loading">Preparing X3D scene…</div>;
  }

  return (
    <x3d-canvas
      key={sceneUrl}
      className="x3d-viewer"
      src={sceneUrl}
      contentScale="auto"
      notifications="false"
      splashScreen="false"
      aria-label="Interactive X3D scene preview"
    />
  );
}
