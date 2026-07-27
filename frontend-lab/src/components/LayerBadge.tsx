import type { SourceLayer } from "../types";

export function LayerBadge({ layer }: { layer: SourceLayer }) {
  return (
    <span className="inline-flex rounded-md border border-white/[0.08] bg-white/[0.03] px-1.5 py-[1px] font-mono text-[10px] tracking-normal text-[#8a8a8a]">
      {layer}
    </span>
  );
}
