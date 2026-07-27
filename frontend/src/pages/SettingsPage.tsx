import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/Button";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import type { InstallationRepo, SettingsResponse } from "../types/api";

export function SettingsPage() {
  const {
    data: apis,
    error: apisError,
    loading: apisLoading,
    reload: reloadApis,
  } = useAsync(() => api.listApis(), []);
  const {
    data: settings,
    error: settingsError,
    loading: settingsLoading,
    reload: reloadSettings,
  } = useAsync(() => api.getSettings(), []);

  const [repos, setRepos] = useState<InstallationRepo[] | null>(null);
  const [reposError, setReposError] = useState<string | null>(null);
  const [reposLoading, setReposLoading] = useState(false);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionOk, setActionOk] = useState<string | null>(null);

  const loadRepos = useCallback(async (cfg: SettingsResponse | null) => {
    if (!cfg?.github_configured) {
      setRepos(null);
      setReposError(null);
      return;
    }
    setReposLoading(true);
    setReposError(null);
    try {
      const data = await api.listRepos();
      setRepos(data.items);
      const current =
        data.items.find((r) => r.connected)?.full_name ??
        data.connected_repo ??
        "";
      setSelected(current);
    } catch (err) {
      setRepos(null);
      setReposError(err instanceof Error ? err.message : String(err));
    } finally {
      setReposLoading(false);
    }
  }, []);

  useEffect(() => {
    if (settings) void loadRepos(settings);
  }, [settings, loadRepos]);

  const error = apisError ?? settingsError;
  if (error) return <ErrorState message={error} />;
  if (apisLoading || settingsLoading || !apis || !settings) {
    return <SkeletonRows rows={2} cols={2} />;
  }

  const primary = apis.find((a) => a.mode === "live") ?? apis[0];
  const connected =
    settings.connected_repo ?? primary?.repo ?? null;

  const rows: Array<{ label: string; value: string }> = [
    {
      label: "GitHub App",
      value: settings.github_configured ? "Configured" : "Not configured",
    },
    { label: "Default base branch", value: settings.default_base_branch },
    {
      label: "Local repo path",
      value: settings.repo_path_set ? "Set" : "Using fixture / API path",
    },
    { label: "Connected repo", value: connected ?? "—" },
    {
      label: "Scheduled watcher",
      value: settings.watch_enabled
        ? `Every ${settings.watch_interval_seconds ?? 300}s`
        : "Disabled",
    },
    { label: "Primary API", value: primary?.id ?? "—" },
    {
      label: "Languages",
      value: (primary?.languages ?? []).join(", ") || "—",
    },
  ];

  async function refreshAll() {
    reloadApis();
    reloadSettings();
  }

  async function onConnect() {
    if (!selected) return;
    setBusy(true);
    setActionError(null);
    setActionOk(null);
    try {
      const doc = await api.connectRepo(selected);
      setActionOk(`Connected ${doc.full_name}`);
      await refreshAll();
      await loadRepos({ ...settings, github_configured: true, connected_repo: doc.full_name });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDisconnect() {
    setBusy(true);
    setActionError(null);
    setActionOk(null);
    try {
      await api.disconnectRepo();
      setActionOk("Disconnected repo");
      setSelected("");
      await refreshAll();
      await loadRepos(settings);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h2 className="text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2]">
          Workspace
        </h2>
        {apis.length === 0 ? (
          <EmptyState message="No watched APIs configured." />
        ) : (
          <div className="max-w-lg overflow-hidden rounded-2xl border border-white/[0.07]">
            {rows.map((row, i) => (
              <div
                key={row.label}
                className={[
                  "flex items-center justify-between gap-4 px-5 py-3.5 text-[13px]",
                  i > 0 ? "border-t border-white/[0.06]" : "",
                ].join(" ")}
              >
                <dt className="text-[#8a8a8a]">{row.label}</dt>
                <dd className="truncate font-mono text-[12px] tracking-normal text-[#a8a8a8]">
                  {row.value}
                </dd>
              </div>
            ))}
            {settings.hint ? (
              <div className="border-t border-white/[0.06] px-5 py-3 text-[12px] text-[#5c5c5c]">
                {settings.hint}
              </div>
            ) : null}
          </div>
        )}
      </section>

      <section className="max-w-lg space-y-3">
        <div>
          <h2 className="text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2]">
            Connect repository
          </h2>
          <p className="mt-1 text-[12px] leading-relaxed text-[#6e6e6e]">
            Pick a repo the GitHub App can access. SelfPI stamps it onto watched
            APIs and opens fix PRs there when breaking changes land.
          </p>
        </div>

        {!settings.github_configured ? (
          <div className="rounded-2xl border border-white/[0.07] px-5 py-4 text-[12px] leading-relaxed text-[#6e6e6e]">
            Configure the GitHub App in <span className="font-mono text-[#8a8a8a]">backend/.env</span>{" "}
            (<span className="font-mono">GITHUB_APP_ID</span>, private key, installation id),
            install it on your repos, then reload Settings.
          </div>
        ) : (
          <div className="space-y-3 rounded-2xl border border-white/[0.07] px-5 py-4">
            {reposLoading ? (
              <p className="text-[12px] text-[#6e6e6e]">Loading installation repos…</p>
            ) : reposError ? (
              <p className="text-[12px] text-[#f2555a]">{reposError}</p>
            ) : !repos || repos.length === 0 ? (
              <p className="text-[12px] text-[#6e6e6e]">
                No repos visible to this App installation. Install the App on a
                repository, then refresh.
              </p>
            ) : (
              <>
                <label className="block space-y-1.5">
                  <span className="text-[11px] uppercase tracking-[0.06em] text-[#5c5c5c]">
                    Repository
                  </span>
                  <select
                    className="h-9 w-full rounded-lg border border-[#2e2e2e] bg-[#0a0a0a] px-3 font-mono text-[12px] text-[#f2f2f2] outline-none focus:border-[#4a4a4a]"
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                    disabled={busy}
                  >
                    <option value="">Select a repo…</option>
                    {repos.map((r) => (
                      <option key={r.full_name} value={r.full_name}>
                        {r.full_name}
                        {r.private ? " (private)" : ""}
                        {r.connected ? " · connected" : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    variant="primary"
                    disabled={busy || !selected || selected === connected}
                    onClick={() => void onConnect()}
                  >
                    {busy ? "Saving…" : "Connect repo"}
                  </Button>
                  {connected ? (
                    <Button
                      variant="ghost"
                      disabled={busy}
                      onClick={() => void onDisconnect()}
                    >
                      Disconnect
                    </Button>
                  ) : null}
                  <Button
                    variant="ghost"
                    disabled={busy || reposLoading}
                    onClick={() => void loadRepos(settings)}
                  >
                    Refresh list
                  </Button>
                </div>
              </>
            )}
            {actionError ? (
              <p className="text-[12px] text-[#f2555a]">{actionError}</p>
            ) : null}
            {actionOk ? (
              <p className="text-[12px] text-[#7aa3c4]">{actionOk}</p>
            ) : null}
          </div>
        )}
      </section>
    </div>
  );
}
