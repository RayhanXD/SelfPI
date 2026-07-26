import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import { DEMO_BUMP_SPEC } from "../lib/demo";
import { apiStatusLabel, apiStatusTone } from "../lib/status";
import { useAsync } from "../lib/useAsync";

function isDemoApi(a: { id: string; mode?: string | null }) {
  return a.mode === "demo" || a.id === "stripe-demo";
}

function isLiveApi(a: { id: string; mode?: string | null }) {
  return a.mode === "live" || (a.mode == null && a.id === "stripe");
}

export function WatchedApisPage() {
  const navigate = useNavigate();
  const { data: apis, error, loading, reload } = useAsync(() => api.listApis(), []);
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const onCheck = async (id: string) => {
    setBusy(`check:${id}`);
    setActionError(null);
    try {
      const result = await api.checkApi(id);
      reload();
      if (result.changes_detected > 0) {
        navigate(`/changes?api_id=${id}`);
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Check failed");
    } finally {
      setBusy(null);
    }
  };

  const onBump = async (id: string) => {
    setBusy(`bump:${id}`);
    setActionError(null);
    try {
      const version = `demo-${Date.now()}`;
      const result = await api.pushSpecVersion(id, version, {
        ...DEMO_BUMP_SPEC,
        info: { ...DEMO_BUMP_SPEC.info, version },
      });
      reload();
      if (result.changes_detected > 0) {
        navigate(`/changes?api_id=${id}`);
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Bump failed");
    } finally {
      setBusy(null);
    }
  };

  if (error || actionError) {
    return <ErrorState message={error ?? actionError!} />;
  }
  if (loading || !apis) return <SkeletonRows />;
  if (apis.length === 0) return <EmptyState message="No APIs watched yet." />;

  return (
    <div className="space-y-3">
      <p className="text-xs text-text-muted">
        <span className="font-mono">Bump spec</span> is demo-only (
        <span className="font-mono">source → payment_method</span>).{" "}
        <span className="font-mono">Check now</span> polls the live Stripe OpenAPI.
      </p>
      <div className="overflow-hidden rounded-md border border-border">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="sticky top-0 bg-surface-2">
            <tr className="border-b border-border text-xs uppercase tracking-wide text-text-muted">
              <th className="px-3 py-2 font-medium">API</th>
              <th className="px-3 py-2 font-medium">Version</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Last checked</th>
              <th className="px-3 py-2 font-medium">Open changes</th>
              <th className="px-3 py-2 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {apis.map((a) => (
              <tr
                key={a.id}
                className="border-b border-border last:border-0 hover:bg-surface-2"
              >
                <td className="px-3 py-2">
                  <Link
                    to={`/changes?api_id=${a.id}`}
                    className="text-text-primary hover:text-accent"
                  >
                    {a.name}
                  </Link>
                  <div className="font-mono text-xs text-text-muted">{a.id}</div>
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
                <td className="px-3 py-2">
                  <div className="flex justify-end gap-2">
                    {isLiveApi(a) ? (
                      <Button
                        onClick={() => onCheck(a.id)}
                        disabled={busy === `check:${a.id}`}
                      >
                        {busy === `check:${a.id}` ? "Checking…" : "Check now"}
                      </Button>
                    ) : null}
                    {isDemoApi(a) ? (
                      <Button
                        variant="primary"
                        onClick={() => onBump(a.id)}
                        disabled={busy === `bump:${a.id}`}
                      >
                        {busy === `bump:${a.id}` ? "Bumping…" : "Bump spec"}
                      </Button>
                    ) : null}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
