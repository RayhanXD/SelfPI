import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { LayerBadge } from "../components/LayerBadge";
import { api } from "../lib/api";
import type { CallSite, ChangeDetail } from "../types/api";

export function CallSiteExplorerPage() {
  const { id } = useParams<{ id: string }>();
  const [change, setChange] = useState<ChangeDetail | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .getChange(id)
      .then(setChange)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  if (error) return <p className="text-danger">{error}</p>;
  if (!change) return <p className="text-text-muted">Loading…</p>;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 text-sm">
        <Link to={`/changes/${change.id}`} className="text-text-muted hover:text-accent">
          ← {change.operation_id}
        </Link>
        <span className="text-text-muted">·</span>
        <span className="text-text-secondary">{change.call_sites.length} records</span>
      </div>

      {change.call_sites.length === 0 ? (
        <p className="text-text-muted">No call sites for this change.</p>
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
              {change.call_sites.map((cs, i) => (
                <CallSiteRow
                  key={`${cs.file}:${cs.span.start_line}:${i}`}
                  site={cs}
                  expanded={expanded === i}
                  onToggle={() => setExpanded(expanded === i ? null : i)}
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
  onToggle,
}: {
  site: CallSite;
  expanded: boolean;
  onToggle: () => void;
}) {
  const args = site.args
    .map((a) => a.name ?? "?")
    .filter(Boolean)
    .join(", ");

  return (
    <>
      <tr
        className={`cursor-pointer border-b border-border hover:bg-surface-2 ${
          expanded ? "bg-surface-3" : ""
        }`}
        onClick={onToggle}
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
            <pre className="overflow-x-auto rounded-sm border border-border bg-bg p-3 font-mono text-xs text-text-secondary">
              {JSON.stringify(site, null, 2)}
            </pre>
          </td>
        </tr>
      ) : null}
    </>
  );
}
