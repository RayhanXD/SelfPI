export function SettingsPage() {
  return (
    <div className="space-y-4 text-sm">
      <p className="text-text-secondary">
        v1 is single-user. Auth and multi-repo settings ship later.
      </p>
      <dl className="max-w-md space-y-3 rounded-lg border border-border bg-surface-1 p-4">
        <div className="flex justify-between gap-4">
          <dt className="text-text-muted">API base</dt>
          <dd className="font-mono text-xs text-text-secondary">/ (proxied)</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-text-muted">Theme</dt>
          <dd className="text-text-secondary">Dark (only)</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-text-muted">Languages</dt>
          <dd className="font-mono text-xs text-text-secondary">python</dd>
        </div>
      </dl>
    </div>
  );
}
