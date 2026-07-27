import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CodeBlock } from "../components/CodeBlock";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { HorizonUnderline } from "../components/HorizonUnderline";
import { LayerBadge } from "../components/LayerBadge";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import type { CallSite } from "../types/api";

export function CallSiteExplorerPage() {
  const { id } = useParams<{ id: string }>();
  const { data: change, error, loading } = useAsync(() => api.getChange(id!), [id]);
  const [expanded, setExpanded] = useState<number | null>(0);
  const [focusIdx, setFocusIdx] = useState(0);

  const sites = change?.call_sites ?? [];

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!sites.length) return;
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
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

  if (error) return <ErrorState message={error} />;
  if (loading || !change) return <SkeletonRows />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3 text-[13px]">
        <Link
          to={`/app/changes/${change.id}`}
          className="text-[#666] transition-colors duration-150 hover:text-[#aaa]"
        >
          ← {change.operation_id}
        </Link>
        <span className="text-[#3a3a3a]">·</span>
        <span className="text-[#8a8a8a]">
          {sites.length} record{sites.length === 1 ? "" : "s"}
        </span>
        <kbd className="ml-auto hidden rounded-md border border-white/[0.08] bg-[#0a0a0a] px-1.5 py-0.5 font-mono text-[11px] tracking-normal text-[#666] sm:inline">
          ↑↓ Enter
        </kbd>
      </div>

      {sites.length === 0 ? (
        <div className="rounded-2xl border border-white/[0.07] px-5 py-10">
          <EmptyState message="No call sites for this change." />
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-white/[0.07]">
          <div className="min-w-[720px]">
            <div className="grid grid-cols-[1.4fr_1fr_0.8fr_0.7fr_0.9fr] gap-2 border-b border-white/[0.06] bg-[#0a0a0a] px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#555]">
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
      )}
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
        className="relative grid w-full grid-cols-[1.4fr_1fr_0.8fr_0.7fr_0.9fr] gap-2 px-4 py-3.5 text-left transition-colors duration-150 hover:bg-white/[0.02]"
      >
        <HorizonUnderline
          show={active}
          className="absolute inset-x-4 bottom-0 h-[2px] rounded-full"
        />
        <span className="truncate font-mono text-[12px] tracking-normal text-white">
          {site.file}:{site.span.start_line}
        </span>
        <span className="truncate font-mono text-[12px] tracking-normal text-[#888]">
          {site.operation_id ?? "—"}
        </span>
        <span className="truncate font-mono text-[12px] tracking-normal text-[#666]">
          {args || "—"}
        </span>
        <span>
          {site.source_layer ? <LayerBadge layer={site.source_layer} /> : "—"}
        </span>
        <span>
          {site.confidence != null ? <ConfidenceBar value={site.confidence} /> : "—"}
        </span>
      </button>
      {expanded ? (
        <div className="space-y-3 border-t border-white/[0.06] bg-black px-4 py-4">
          {site.snippet ? (
            <pre className="overflow-x-auto whitespace-pre font-mono text-[12px] tracking-normal text-[#a8a8a8]">
              {site.snippet}
            </pre>
          ) : null}
          <CodeBlock>{JSON.stringify(site, null, 2)}</CodeBlock>
        </div>
      ) : null}
    </div>
  );
}
