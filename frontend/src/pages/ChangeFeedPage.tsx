import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { changeStatusLabel } from "../lib/status";
import type { ChangeSummary } from "../types/api";
import { StatusPill } from "../components/StatusPill";

function statusTone(status: ChangeSummary["status"]) {
  if (status === "merged") return "ok" as const;
  if (status === "pr_open") return "info" as const;
  if (status === "dismissed") return "muted" as const;
  if (status === "scanning") return "warn" as const;
  return "warn" as const;
}

export function ChangeFeedPage() {
  const [params] = useSearchParams();
  const apiId = params.get("api_id") ?? undefined;
  const [items, setItems] = useState<ChangeSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setError(null);
    api
      .listChanges({ api_id: apiId })
      .then((res) => setItems(res.items))
      .catch((e: Error) => setError(e.message));
  }, [apiId]);

  if (error) return <p className="text-danger">{error}</p>;
  if (!items) return <p className="text-text-muted">Loading…</p>;
  if (items.length === 0) {
    return <p className="text-text-muted">No changes detected yet.</p>;
  }

  return (
    <div className="overflow-hidden rounded-md border border-border">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="sticky top-0 bg-surface-2">
          <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
            <th className="px-3 py-2 font-medium">API</th>
            <th className="px-3 py-2 font-medium">Operation</th>
            <th className="px-3 py-2 font-medium">Kind</th>
            <th className="px-3 py-2 font-medium">Call sites</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 font-medium">Detected</th>
          </tr>
        </thead>
        <tbody>
          {items.map((c) => (
            <tr
              key={c.id}
              className="border-b border-border last:border-0 hover:bg-surface-2"
            >
              <td className="px-3 py-2 text-text-secondary">{c.api_id}</td>
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
                <StatusPill label={changeStatusLabel(c.status)} tone={statusTone(c.status)} />
              </td>
              <td className="px-3 py-2 font-mono text-xs text-text-muted">
                {c.detected_at ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
