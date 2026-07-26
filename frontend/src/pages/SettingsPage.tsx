import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";

export function SettingsPage() {
  const {
    data: apis,
    error: apisError,
    loading: apisLoading,
  } = useAsync(() => api.listApis(), []);
  const {
    data: settings,
    error: settingsError,
    loading: settingsLoading,
  } = useAsync(() => api.getSettings(), []);

  const error = apisError ?? settingsError;
  if (error) return <ErrorState message={error} />;
  if (apisLoading || settingsLoading || !apis || !settings) {
    return <SkeletonRows rows={2} cols={2} />;
  }

  const primary = apis.find((a) => a.mode === "demo") ?? apis[0];

  return (
    <div className="space-y-4 text-sm">
      <p className="text-text-secondary">
        v1 is single-user. Connect a repo via the GitHub App env vars (no OAuth UI yet).
      </p>
      {apis.length === 0 ? (
        <EmptyState message="No watched APIs configured. Run make reset / make seed." />
      ) : (
        <dl className="max-w-lg space-y-3 rounded-lg border border-border bg-surface-1 p-4">
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">GitHub App</dt>
            <dd className="font-mono text-xs text-text-secondary">
              {settings.github_configured ? "configured" : "not configured"}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">Default base branch</dt>
            <dd className="font-mono text-xs text-text-secondary">
              {settings.default_base_branch}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-text-muted">REPO_PATH set</dt>
            <dd className="font-mono text-xs text-text-secondary">
              {settings.repo_path_set ? "yes" : "no (uses fixture / api repo_path)"}
            </dd>
          </div>
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
            <dt className="text-text-muted">Theme</dt>
            <dd className="text-text-secondary">Dark (only)</dd>
          </div>
          {settings.hint ? (
            <div className="border-t border-border pt-3 text-xs text-text-muted">
              {settings.hint}
            </div>
          ) : null}
        </dl>
      )}
    </div>
  );
}
