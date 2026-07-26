import type { SourceLayer } from "../types/api";

interface LayerBadgeProps {
  layer: SourceLayer;
}

export function LayerBadge({ layer }: LayerBadgeProps) {
  return (
    <span className="inline-flex rounded-sm border border-border bg-surface-2 px-1.5 py-0.5 font-mono text-xs text-text-secondary">
      {layer}
    </span>
  );
}
