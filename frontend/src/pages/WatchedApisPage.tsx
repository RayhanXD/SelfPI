import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { apiStatusLabel, apiStatusTone } from "../lib/status";
import type { ApiSummary } from "../types/api";
import { StatusPill } from "../components/StatusPill";

export function WatchedApisPage() {
  const [apis, setApis] = useState<ApiSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState<string | null>(null);

  const load = () => {
    setError(null);
    api
      .listApis()
      .then(setApis)
      .catch((e: Error) => setError(e.message));
  };

  useEffect(load, []);

  const onCheck = async (id: string) => {
    setChecking(id);
    try {
      await api.checkApi(id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Check failed");
    } finally {
      setChecking(null);
    }
  };

  if (error) {
    return <p className="text-danger">{error}</p>;
  }

  if (!apis) {
    return <p className="text-text-muted">Loading…</p>;
  }

  if (apis.length === 0) {
    return <p className="text-text-muted">No APIs watched yet.</p>;
  }

  return (
    <div className="overflow-hidden rounded-md border border-border">
      <table className="w-full border-collapse text-left text-sm">
        <thead className="sticky top-0 bg-surface-2">
          <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
            <th className="px-3 py-2 font-medium">API</th>
            <th className="px-3 py-2 font-medium">Version</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 font-medium">Last checked</th>
            <th className="px-3 py-2 font-medium">Open changes</th>
            <th className="px-3 py-2 font-medium" />
          </tr>
        </thead>
        <tbody>
          {apis.map((a) => (
            <tr
              key={a.id}
              className="border-b border-border last:border-0 hover:bg-surface-2"
            >
              <td className="px-3 py-2">
                <Link to={`/changes?api_id=${a.id}`} className="text-text-primary hover:text-accent">
                  {a.name}
                </Link>
              </td>
              <td className="px-3 py-2 font-mono text-text-secondary">
                {a.current_version ?? "—"}
              </td>
              <td className="px-3 py-2">
                <StatusPill label={apiStatusLabel(a.status)} tone={apiStatusTone(a.status)} />
              </td>
              <td className="px-3 py-2 font-mono text-xs text-text-muted">
                {a.last_checked ?? "—"}
              </td>
              <td className="px-3 py-2 tabular-nums text-text-secondary">
                {a.open_change_count}
              </td>
              <td className="px-3 py-2 text-right">
                <button
                  type="button"
                  onClick={() => onCheck(a.id)}
                  disabled={checking === a.id}
                  className="rounded-md border border-border-strong px-2.5 py-1 text-xs text-text-secondary hover:bg-surface-3 disabled:opacity-50"
                >
                  {checking === a.id ? "Checking…" : "Check now"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
