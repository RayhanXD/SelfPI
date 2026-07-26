import { Link, useSearchParams } from "react-router-dom";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import { changeStatusLabel, changeStatusTone } from "../lib/status";
import { useAsync } from "../lib/useAsync";
import type { ChangeStatus } from "../types/api";

const FILTERS: Array<{ value: string; label: string }> = [
  { value: "", label: "All" },
  { value: "detected", label: "Detected" },
  { value: "scanning", label: "Scanning" },
  { value: "pr_open", label: "PR open" },
  { value: "merged", label: "Merged" },
  { value: "dismissed", label: "Dismissed" },
];

export function ChangeFeedPage() {
  const [params, setParams] = useSearchParams();
  const apiId = params.get("api_id") ?? undefined;
  const status = params.get("status") ?? undefined;

  const { data, error, loading } = useAsync(
    () => api.listChanges({ api_id: apiId, status }),
    [apiId, status],
  );

  const setStatus = (next: string) => {
    const p = new URLSearchParams(params);
    if (next) p.set("status", next);
    else p.delete("status");
    setParams(p);
  };

  if (error) return <ErrorState message={error} />;
  if (loading || !data) return <SkeletonRows />;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {apiId ? (
          <span className="rounded-sm border border-border bg-surface-1 px-2 py-0.5 font-mono text-xs text-text-secondary">
            api_id={apiId}
            <button
              type="button"
              className="ml-2 text-text-muted hover:text-accent"
              onClick={() => {
                const p = new URLSearchParams(params);
                p.delete("api_id");
                setParams(p);
              }}
            >
              ×
            </button>
          </span>
        ) : null}
        <div className="flex flex-wrap gap-1">
          {FILTERS.map((f) => (
            <button
              key={f.value || "all"}
              type="button"
              onClick={() => setStatus(f.value)}
              className={[
                "rounded-sm border px-2 py-0.5 text-xs",
                (status ?? "") === f.value
                  ? "border-accent bg-surface-3 text-text-primary"
                  : "border-border text-text-muted hover:bg-surface-2",
              ].join(" ")}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {data.items.length === 0 ? (
        <EmptyState message="No changes detected yet." />
      ) : (
        <div className="overflow-hidden rounded-md border border-border">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 bg-surface-2">
              <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
                <th className="px-3 py-2 font-medium">API</th>
                <th className="px-3 py-2 font-medium">Operation</th>
                <th className="px-3 py-2 font-medium">Kind</th>
                <th className="px-3 py-2 font-medium">Call sites</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">PR</th>
                <th className="px-3 py-2 font-medium">Detected</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-border last:border-0 hover:bg-surface-2"
                >
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">
                    {c.api_id}
                  </td>
                  <td className="px-3 py-2">
                    <Link
                      to={`/changes/${c.id}`}
                      className="font-mono text-text-primary hover:text-accent"
                    >
                      {c.operation_id}
                    </Link>
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">{c.kind}</td>
                  <td className="px-3 py-2 tabular-nums text-text-secondary">
                    {c.call_site_count}
                  </td>
                  <td className="px-3 py-2">
                    <StatusPill
                      label={changeStatusLabel(c.status as ChangeStatus)}
                      tone={changeStatusTone(c.status as ChangeStatus)}
                    />
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-text-muted">
                    {c.pr ? `#${c.pr.number}` : "—"}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-text-muted">
                    {c.detected_at ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
