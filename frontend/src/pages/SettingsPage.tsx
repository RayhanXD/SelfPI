import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Button } from "../components/Button";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { api, resolveApiUrl } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useAsync } from "../lib/useAsync";
import type { InstallationRepo, SettingsResponse } from "../types/api";

export function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { reload: reloadAuth, logout, loginHrefFor } = useAuth();
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
    if (cfg.login_required && !cfg.authenticated) {
      setRepos(null);
      setReposError(null);
      return;
    }
    if (!cfg.app_installed) {
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

  // After GitHub Install App redirect (?installed=1), sync + refresh.
  useEffect(() => {
    const installed = searchParams.get("installed");
    if (installed !== "1" && installed !== "0") return;

    void (async () => {
      setBusy(true);
      setActionError(null);
      try {
        if (installed === "1") {
          await api.syncInstallation();
          setActionOk("SelfPI is installed on GitHub. Pick a repository below.");
        } else {
          setActionError(
            searchParams.get("reason") === "no_installation"
              ? "Install did not complete — try Install SelfPI on GitHub again."
              : "Could not confirm the App installation."
          );
        }
        await reloadAuth();
        reloadSettings();
      } catch (err) {
        setActionError(err instanceof Error ? err.message : String(err));
      } finally {
        setBusy(false);
        const next = new URLSearchParams(searchParams);
        next.delete("installed");
        next.delete("setup_action");
        next.delete("reason");
        setSearchParams(next, { replace: true });
      }
    })();
  }, [searchParams, setSearchParams, reloadAuth, reloadSettings]);

  const error = apisError ?? settingsError;
  if (error) return <ErrorState message={error} />;
  if (apisLoading || settingsLoading || !apis || !settings) {
    return <SkeletonRows rows={2} cols={2} />;
  }

  const primary = apis.find((a) => a.mode === "live") ?? apis[0];
  const connected = settings.connected_repo ?? primary?.repo ?? null;
  const needsLogin = Boolean(settings.login_required && !settings.authenticated);
  const needsInstall = Boolean(
    settings.github_configured &&
      settings.authenticated &&
      !settings.app_installed
  );
  const installHref = resolveApiUrl(settings.install_url || "/auth/github/install");
  const loginHref = settings.oauth_configured
    ? loginHrefFor("/app/settings")
    : null;

  const rows: Array<{ label: string; value: string }> = [
    {
      label: "Signed in",
      value: settings.user?.login
        ? `@${settings.user.login}`
        : settings.oauth_configured
          ? "Not signed in"
          : "OAuth not configured",
    },
    {
      label: "GitHub App",
      value: !settings.github_configured
        ? "Not configured"
        : settings.app_installed
          ? "Installed"
          : "Ready — install on GitHub",
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
    await reloadAuth();
  }

  async function onLogout() {
    setBusy(true);
    setActionError(null);
    try {
      await logout();
      setActionOk("Signed out.");
      setRepos(null);
      await refreshAll();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onSyncInstall() {
    setBusy(true);
    setActionError(null);
    setActionOk(null);
    try {
      const status = await api.syncInstallation();
      if (status.app_installed) {
        setActionOk("Found your GitHub App installation.");
      } else {
        setActionError("No installation found yet — install SelfPI on GitHub first.");
      }
      await refreshAll();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onConnect() {
    if (!selected) return;
    setBusy(true);
    setActionError(null);
    setActionOk(null);
    try {
      const doc = await api.connectRepo(selected);
      const detected = doc.detected_apis?.length
        ? ` Detected: ${doc.detected_apis.join(", ")}.`
        : " No catalog APIs detected in the local checkout.";
      const unwatch = doc.unwatchable?.length
        ? ` Needs OpenAPI URL: ${doc.unwatchable.join(", ")}.`
        : "";
      setActionOk(`Connected ${doc.full_name}.${detected}${unwatch}`);
      await refreshAll();
      await loadRepos({
        ...settings!,
        github_configured: true,
        app_installed: true,
        connected_repo: doc.full_name,
        authenticated: true,
      });
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
      <section className="max-w-lg space-y-3">
        <div>
          <h2 className="text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2]">
            Account
          </h2>
          <p className="mt-1 text-[12px] leading-relaxed text-[#6e6e6e]">
            Sign in with GitHub, install SelfPI on the repos you care about, then
            connect one here.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-white/[0.07] px-5 py-4">
          {settings.user?.avatar_url ? (
            <img
              src={settings.user.avatar_url}
              alt=""
              className="h-8 w-8 rounded-full border border-white/[0.08]"
            />
          ) : null}
          <div className="min-w-0 flex-1">
            <div className="truncate text-[13px] text-[#f2f2f2]">
              {settings.user
                ? settings.user.name || `@${settings.user.login}`
                : "Not signed in"}
            </div>
            {settings.user?.login ? (
              <div className="font-mono text-[11px] text-[#6e6e6e]">
                @{settings.user.login}
              </div>
            ) : null}
          </div>
          {settings.authenticated ? (
            <Button variant="ghost" disabled={busy} onClick={() => void onLogout()}>
              Sign out
            </Button>
          ) : settings.oauth_configured && loginHref ? (
            <a
              href={loginHref}
              className="inline-flex h-8 items-center rounded-lg bg-[#f2f2f2] px-3 text-[12px] font-medium text-[#0a0a0a] hover:bg-white"
            >
              Login with GitHub
            </a>
          ) : (
            <span className="text-[12px] text-[#5c5c5c]">
              Set GITHUB_CLIENT_ID / SECRET
            </span>
          )}
        </div>
      </section>

      {needsInstall ? (
        <section className="max-w-lg space-y-3">
          <div>
            <h2 className="text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2]">
              Install SelfPI
            </h2>
            <p className="mt-1 text-[12px] leading-relaxed text-[#6e6e6e]">
              Grant SelfPI access to the repositories you want watched. After
              install, GitHub returns you here to connect a repo.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-white/[0.07] px-5 py-4">
            <a
              href={installHref}
              className="inline-flex h-8 items-center rounded-lg bg-[#f2f2f2] px-3 text-[12px] font-medium text-[#0a0a0a] hover:bg-white"
            >
              Install SelfPI on GitHub
            </a>
            <Button
              variant="ghost"
              disabled={busy}
              onClick={() => void onSyncInstall()}
            >
              I already installed — refresh
            </Button>
          </div>
        </section>
      ) : null}

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
            Configure the GitHub App on the server in{" "}
            <span className="font-mono text-[#8a8a8a]">backend/.env</span> (
            <span className="font-mono">GITHUB_APP_ID</span>, private key). Users
            install the App from this screen — no{" "}
            <span className="font-mono">INSTALLATION_ID</span> required.
          </div>
        ) : needsLogin ? (
          <div className="space-y-3 rounded-2xl border border-white/[0.07] px-5 py-4">
            <p className="text-[12px] leading-relaxed text-[#6e6e6e]">
              Sign in with GitHub to install the App and connect repositories.
            </p>
            {loginHref ? (
              <a
                href={loginHref}
                className="inline-flex h-8 items-center rounded-lg bg-[#f2f2f2] px-3 text-[12px] font-medium text-[#0a0a0a] hover:bg-white"
              >
                Login with GitHub
              </a>
            ) : null}
          </div>
        ) : needsInstall ? (
          <div className="rounded-2xl border border-white/[0.07] px-5 py-4 text-[12px] leading-relaxed text-[#6e6e6e]">
            Install SelfPI on GitHub first (section above), then connect a repo.
          </div>
        ) : (
          <div className="space-y-3 rounded-2xl border border-white/[0.07] px-5 py-4">
            {reposLoading ? (
              <p className="text-[12px] text-[#6e6e6e]">Loading installation repos…</p>
            ) : reposError ? (
              <div className="space-y-2">
                <p className="text-[12px] text-[#f2555a]">{reposError}</p>
                <div className="flex flex-wrap gap-2">
                  <a
                    href={installHref}
                    className="inline-flex h-8 items-center rounded-lg border border-white/[0.1] px-3 text-[12px] text-[#f2f2f2] hover:bg-white/[0.04]"
                  >
                    Install / update on GitHub
                  </a>
                  <Button
                    variant="ghost"
                    disabled={busy}
                    onClick={() => void onSyncInstall()}
                  >
                    Refresh installation
                  </Button>
                </div>
              </div>
            ) : !repos || repos.length === 0 ? (
              <div className="space-y-2">
                <p className="text-[12px] text-[#6e6e6e]">
                  No repos visible to this App installation. Add repositories on
                  GitHub, then refresh.
                </p>
                <a
                  href={installHref}
                  className="inline-flex h-8 items-center rounded-lg border border-white/[0.1] px-3 text-[12px] text-[#f2f2f2] hover:bg-white/[0.04]"
                >
                  Configure repos on GitHub
                </a>
              </div>
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
          </div>
        )}
        {actionError ? (
          <p className="text-[12px] text-[#f2555a]">{actionError}</p>
        ) : null}
        {actionOk ? (
          <p className="text-[12px] text-[#7aa3c4]">{actionOk}</p>
        ) : null}
      </section>
    </div>
  );
}
