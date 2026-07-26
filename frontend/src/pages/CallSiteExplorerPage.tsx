import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CodeBlock } from "../components/CodeBlock";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
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
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <Link to={`/changes/${change.id}`} className="text-text-muted hover:text-accent">
          ← {change.operation_id}
        </Link>
        <span className="text-text-muted">·</span>
        <span className="text-text-secondary">{sites.length} records</span>
        <span className="ml-auto text-xs text-text-muted">
          ↑↓ navigate · Enter expand
        </span>
      </div>

      {sites.length === 0 ? (
        <EmptyState message="No call sites for this change." />
      ) : (
        <div className="overflow-hidden rounded-md border border-border">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 bg-surface-2">
              <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
                <th className="px-3 py-2 font-medium">Location</th>
                <th className="px-3 py-2 font-medium">operation_id</th>
                <th className="px-3 py-2 font-medium">Args</th>
                <th className="px-3 py-2 font-medium">Layer</th>
                <th className="px-3 py-2 font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
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
            </tbody>
          </table>
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

  return (
    <>
      <tr
        className={[
          "cursor-pointer border-b border-border hover:bg-surface-2",
          expanded || focused ? "bg-surface-3" : "",
        ].join(" ")}
        onClick={onToggle}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
        }}
      >
        <td className="px-3 py-2 font-mono text-xs text-text-primary">
          {site.file}:{site.span.start_line}
        </td>
        <td className="px-3 py-2 font-mono text-xs text-text-secondary">
          {site.operation_id ?? "—"}
        </td>
        <td className="px-3 py-2 font-mono text-xs text-text-muted">{args || "—"}</td>
        <td className="px-3 py-2">
          {site.source_layer ? <LayerBadge layer={site.source_layer} /> : "—"}
        </td>
        <td className="px-3 py-2">
          {site.confidence != null ? <ConfidenceBar value={site.confidence} /> : "—"}
        </td>
      </tr>
      {expanded ? (
        <tr className="border-b border-border bg-surface-1">
          <td colSpan={5} className="px-3 py-3">
            {site.snippet ? (
              <pre className="mb-3 overflow-x-auto rounded-sm border border-border bg-bg px-2 py-1 font-mono text-xs text-text-secondary whitespace-pre">
                {site.snippet}
              </pre>
            ) : null}
            <CodeBlock>{JSON.stringify(site, null, 2)}</CodeBlock>
          </td>
        </tr>
      ) : null}
    </>
  );
}
