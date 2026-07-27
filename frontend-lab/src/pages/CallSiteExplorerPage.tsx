import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CodeBlock } from "../components/CodeBlock";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { LayerBadge } from "../components/LayerBadge";
import { MOCK_CHANGE_DETAIL } from "../data/mock";
import { HORIZON } from "../lib/accents";
import type { CallSite } from "../types";

export function CallSiteExplorerPage() {
  const change = MOCK_CHANGE_DETAIL;
  const sites = change.call_sites;
  const [expanded, setExpanded] = useState<number | null>(0);
  const [focusIdx, setFocusIdx] = useState(0);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!sites.length) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setFocusIdx((i) => Math.min(sites.length - 1, i + 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setFocusIdx((i) => Math.max(0, i - 1));
      } else if (e.key === "Enter") {
        e.preventDefault();
        setExpanded((cur) => (cur === focusIdx ? null : focusIdx));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sites.length, focusIdx]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3 text-[13px]">
        <Link
          to={`/changes/${change.id}`}
          className="text-[#666] transition-colors duration-150 hover:text-[#aaa]"
        >
          ← {change.operation_id}
        </Link>
        <span className="text-[#555]">·</span>
        <span className="text-[#888]">{sites.length} records</span>
        <kbd className="ml-auto rounded-md border border-white/[0.08] bg-[#0a0a0a] px-1.5 py-0.5 font-mono text-[11px] text-[#666]">
          ↑↓ Enter
        </kbd>
      </div>

      <div className="overflow-hidden rounded-xl border border-white/[0.08]">
        <div className="grid grid-cols-[1.4fr_1fr_0.8fr_0.7fr_0.9fr] gap-2 border-b border-white/[0.06] bg-[#0a0a0a] px-4 py-2 text-[11px] font-medium uppercase tracking-[0.06em] text-[#555]">
          <div>Location</div>
          <div>operation_id</div>
          <div>Args</div>
          <div>Layer</div>
          <div>Confidence</div>
        </div>
        <div>
          {sites.map((cs, i) => (
            <CallSiteRow
              key={`${cs.file}:${cs.span.start_line}:${i}`}
              site={cs}
              expanded={expanded === i}
              focused={focusIdx === i}
              onToggle={() => {
                setFocusIdx(i);
                setExpanded(expanded === i ? null : i);
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function CallSiteRow({
  site,
  expanded,
  focused,
  onToggle,
}: {
  site: CallSite;
  expanded: boolean;
  focused: boolean;
  onToggle: () => void;
}) {
  const args = site.args
    .map((a) => a.name ?? "?")
    .filter(Boolean)
    .join(", ");
  const active = expanded || focused;

  return (
    <div
      className={[
        "border-b border-white/[0.06] last:border-0",
        active ? "bg-white/[0.03]" : "",
      ].join(" ")}
    >
      <button
        type="button"
        onClick={onToggle}
        className="relative grid w-full grid-cols-[1.4fr_1fr_0.8fr_0.7fr_0.9fr] gap-2 px-4 py-3 text-left transition-colors duration-150 hover:bg-white/[0.02]"
      >
        {active ? (
          <span
            aria-hidden
            className="absolute inset-x-4 bottom-0 h-[2px] rounded-full"
            style={{ backgroundImage: HORIZON }}
          />
        ) : null}
        <span className="truncate font-mono text-[12px] text-white">
          {site.file}:{site.span.start_line}
        </span>
        <span className="truncate font-mono text-[12px] text-[#888]">
          {site.operation_id ?? "—"}
        </span>
        <span className="truncate font-mono text-[12px] text-[#666]">{args || "—"}</span>
        <span>{site.source_layer ? <LayerBadge layer={site.source_layer} /> : "—"}</span>
        <span>
          {site.confidence != null ? <ConfidenceBar value={site.confidence} /> : "—"}
        </span>
      </button>
      {expanded ? (
        <div className="space-y-3 border-t border-white/[0.06] bg-black px-4 py-3">
          {site.snippet ? (
            <pre className="overflow-x-auto whitespace-pre font-mono text-[12px] text-[#a1a1a1]">
              {site.snippet}
            </pre>
          ) : null}
          <CodeBlock>{JSON.stringify(site, null, 2)}</CodeBlock>
        </div>
      ) : null}
    </div>
  );
}
