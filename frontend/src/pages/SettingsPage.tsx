import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";

export function SettingsPage() {
  const { data: apis, error, loading } = useAsync(() => api.listApis(), []);

  if (error) return <ErrorState message={error} />;
  if (loading || !apis) return <SkeletonRows rows={2} cols={2} />;

  const primary = apis[0];

  return (
    <div className="space-y-4 text-sm">
      <p className="text-text-secondary">
        v1 is single-user. Auth beyond the GitHub App ships later.
      </p>
      {apis.length === 0 ? (
        <EmptyState message="No watched APIs configured. Seed the backend database first." />
      ) : (
        <dl className="max-w-lg space-y-3 rounded-lg border border-border bg-surface-1 p-4">
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">Connected repo</dt>
            <dd className="font-mono text-xs text-text-secondary">{primary?.repo ?? "—"}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">Primary API</dt>
            <dd className="font-mono text-xs text-text-secondary">{primary?.id ?? "—"}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">Languages</dt>
            <dd className="font-mono text-xs text-text-secondary">
              {(primary?.languages ?? []).join(", ") || "—"}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">API base</dt>
            <dd className="font-mono text-xs text-text-secondary">/ (proxied)</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">Theme</dt>
            <dd className="text-text-secondary">Dark (only)</dd>
          </div>
        </dl>
      )}
    </div>
  );
}
