import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { Link } from "react-router-dom";
import { api, resolveApiUrl } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useWorkspace } from "../lib/workspace";
import type { InstallationRepo } from "../types/api";
import { GitHubMark } from "./GitHubMark";

type ListState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; items: InstallationRepo[] };

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      viewBox="0 0 12 12"
      className={[
        "h-3 w-3 shrink-0 text-[#5c5c5c] transition-transform duration-200 ease-[var(--ease-out-expo)]",
        open ? "rotate-180" : "",
      ].join(" ")}
      aria-hidden
    >
      <path
        d="M2.5 4.25L6 7.75l3.5-3.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg viewBox="0 0 12 12" className="h-3 w-3 shrink-0 text-[#5c5c5c]" aria-hidden>
      <path
        d="M3.75 5.25V4a2.25 2.25 0 014.5 0v1.25M3.5 5.25h5A1.25 1.25 0 019.75 6.5v3A1.25 1.25 0 018.5 10.75h-5A1.25 1.25 0 012.25 9.5v-3A1.25 1.25 0 013.5 5.25z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function RepoSwitcher() {
  const listboxId = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const { loginHrefFor } = useAuth();
  const { connectedRepo, settings, switchRepo, loading: workspaceLoading } =
    useWorkspace();

  const [open, setOpen] = useState(false);
  const [list, setList] = useState<ListState>({ status: "idle" });
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [switching, setSwitching] = useState<string | null>(null);
  const [switchError, setSwitchError] = useState<string | null>(null);

  const needsLogin = Boolean(settings?.login_required && !settings?.authenticated);
  const needsInstall = Boolean(
    settings?.github_configured && settings?.authenticated && !settings?.app_installed,
  );
  const githubReady = Boolean(settings?.github_configured && settings?.app_installed);
  const installHref = resolveApiUrl(settings?.install_url || "/auth/github/install");
  const loginHref = settings?.oauth_configured ? loginHrefFor("/app") : null;

  const loadRepos = useCallback(async () => {
    if (workspaceLoading || !settings) {
      setList({ status: "loading" });
      return;
    }
    if (!settings.github_configured) {
      setList({
        status: "error",
        message: "GitHub App is not configured on the server.",
      });
      return;
    }
    if (needsLogin) {
      setList({ status: "error", message: "Sign in with GitHub to list repositories." });
      return;
    }
    if (needsInstall) {
      setList({
        status: "error",
        message: "Install SelfPI on GitHub, then pick a repository.",
      });
      return;
    }
    setList({ status: "loading" });
    try {
      const data = await api.listRepos();
      setList({ status: "ready", items: data.items });
      const connectedIdx = data.items.findIndex((r) => r.connected);
      setActiveIndex(connectedIdx >= 0 ? connectedIdx : 0);
    } catch (err) {
      setList({
        status: "error",
        message: err instanceof Error ? err.message : "Could not load repositories.",
      });
    }
  }, [settings, needsLogin, needsInstall, workspaceLoading]);

  useEffect(() => {
    if (!open) return;
    void loadRepos();
    setQuery("");
    setSwitchError(null);
    const t = window.setTimeout(() => searchRef.current?.focus(), 20);
    return () => window.clearTimeout(t);
  }, [open, loadRepos]);

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        panelRef.current?.contains(target) ||
        triggerRef.current?.contains(target)
      ) {
        return;
      }
      setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const filtered =
    list.status === "ready"
      ? list.items.filter((r) => {
          const q = query.trim().toLowerCase();
          if (!q) return true;
          return (
            r.full_name.toLowerCase().includes(q) ||
            r.owner.toLowerCase().includes(q) ||
            r.name.toLowerCase().includes(q)
          );
        })
      : [];

  useEffect(() => {
    setActiveIndex((i) => {
      if (filtered.length === 0) return 0;
      return Math.min(i, filtered.length - 1);
    });
  }, [filtered.length, query]);

  async function onSelect(fullName: string) {
    if (fullName === connectedRepo || switching) return;
    setSwitching(fullName);
    setSwitchError(null);
    try {
      await switchRepo(fullName);
      setOpen(false);
      triggerRef.current?.focus();
    } catch (err) {
      setSwitchError(err instanceof Error ? err.message : "Switch failed");
    } finally {
      setSwitching(null);
    }
  }

  function onTriggerKeyDown(e: ReactKeyboardEvent<HTMLButtonElement>) {
    if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setOpen(true);
    }
  }

  function onListKeyDown(e: ReactKeyboardEvent<HTMLDivElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, Math.max(filtered.length - 1, 0)));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const item = filtered[activeIndex];
      if (item) void onSelect(item.full_name);
    } else if (e.key === "Home") {
      e.preventDefault();
      setActiveIndex(0);
    } else if (e.key === "End") {
      e.preventDefault();
      setActiveIndex(Math.max(filtered.length - 1, 0));
    }
  }

  const label = connectedRepo ?? "Select repository";
  const statusLabel = connectedRepo ? "Connected" : "Not connected";
  const statusTone = connectedRepo ? "ok" : "muted";

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        onClick={() => setOpen((v) => !v)}
        onKeyDown={onTriggerKeyDown}
        className={[
          "group flex max-w-[min(100vw-2rem,280px)] items-center gap-2.5 rounded-xl border px-2.5 py-1.5 text-left transition-[background-color,border-color] duration-150",
          open
            ? "border-white/[0.12] bg-white/[0.05]"
            : "border-white/[0.07] bg-[#0a0a0a] hover:border-white/[0.12] hover:bg-white/[0.03]",
        ].join(" ")}
      >
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/[0.06] bg-white/[0.03] text-[#a8a8a8]">
          <GitHubMark className="h-3.5 w-3.5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-1.5">
            <span
              className={[
                "inline-block h-1.5 w-1.5 shrink-0 rounded-full",
                statusTone === "ok" ? "bg-ok" : "bg-[#3a3a3a]",
              ].join(" ")}
              aria-hidden
            />
            <span className="text-[10px] font-medium uppercase tracking-[0.08em] text-[#5c5c5c]">
              {workspaceLoading && !connectedRepo ? "Loading…" : statusLabel}
            </span>
          </span>
          <span className="mt-0.5 block truncate font-mono text-[12px] tracking-normal text-[#f2f2f2]">
            {label}
          </span>
        </span>
        <Chevron open={open} />
      </button>

      {open ? (
        <div
          ref={panelRef}
          id={listboxId}
          role="listbox"
          aria-label="Repositories"
          tabIndex={-1}
          onKeyDown={onListKeyDown}
          className="absolute right-0 z-50 mt-2 w-[min(calc(100vw-2rem),320px)] origin-top-right animate-[repo-switcher-in_160ms_var(--ease-out-expo)] overflow-hidden rounded-xl border border-white/[0.08] bg-[#0c0c0c] shadow-[0_16px_48px_rgba(0,0,0,0.55)]"
        >
          <div className="border-b border-white/[0.06] px-3 py-2.5">
            <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#4a4a4a]">
              Workspace target
            </div>
            {githubReady ? (
              <label className="mt-2 block">
                <span className="sr-only">Filter repositories</span>
                <input
                  ref={searchRef}
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Filter owner/name…"
                  className="h-8 w-full rounded-lg border border-white/[0.08] bg-[#050505] px-2.5 font-mono text-[12px] tracking-normal text-[#f2f2f2] placeholder:text-[#4a4a4a] outline-none focus:border-[#3d3d3d]"
                  autoComplete="off"
                  spellCheck={false}
                />
              </label>
            ) : null}
          </div>

          <div className="max-h-[min(50vh,280px)] overflow-y-auto py-1">
            {list.status === "loading" || list.status === "idle" ? (
              <div className="space-y-2 px-3 py-3" aria-busy="true" aria-live="polite">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-9 animate-pulse rounded-lg bg-white/[0.04]"
                    style={{ animationDelay: `${i * 80}ms` }}
                  />
                ))}
                <p className="text-[11px] text-[#5c5c5c]">Loading repositories…</p>
              </div>
            ) : list.status === "error" ? (
              <div className="space-y-3 px-3 py-3">
                <p className="text-[12px] leading-relaxed text-[#a8a8a8]">
                  {list.message}
                </p>
                <div className="flex flex-wrap gap-2">
                  {needsLogin && loginHref ? (
                    <a
                      href={loginHref}
                      className="inline-flex h-7 items-center rounded-md bg-[#f2f2f2] px-2.5 text-[11px] font-medium text-[#0a0a0a] hover:bg-white"
                    >
                      Login with GitHub
                    </a>
                  ) : null}
                  {needsInstall || !settings?.app_installed ? (
                    <a
                      href={installHref}
                      className="inline-flex h-7 items-center rounded-md border border-white/[0.1] px-2.5 text-[11px] text-[#f2f2f2] hover:bg-white/[0.04]"
                    >
                      Install on GitHub
                    </a>
                  ) : null}
                  <Link
                    to="/app/settings"
                    onClick={() => setOpen(false)}
                    className="inline-flex h-7 items-center rounded-md border border-white/[0.1] px-2.5 text-[11px] text-[#8a8a8a] hover:text-[#f2f2f2]"
                  >
                    Open Settings
                  </Link>
                </div>
              </div>
            ) : filtered.length === 0 ? (
              <div className="space-y-3 px-3 py-3">
                <p className="text-[12px] leading-relaxed text-[#6e6e6e]">
                  {query.trim()
                    ? "No repositories match that filter."
                    : "No repositories visible to this App installation."}
                </p>
                {!query.trim() ? (
                  <a
                    href={installHref}
                    className="inline-flex h-7 items-center rounded-md border border-white/[0.1] px-2.5 text-[11px] text-[#f2f2f2] hover:bg-white/[0.04]"
                  >
                    Configure repos on GitHub
                  </a>
                ) : null}
              </div>
            ) : (
              <ul className="px-1">
                {filtered.map((repo, idx) => {
                  const isCurrent = repo.full_name === connectedRepo;
                  const isActive = idx === activeIndex;
                  const isBusy = switching === repo.full_name;
                  return (
                    <li key={repo.full_name}>
                      <button
                        type="button"
                        role="option"
                        aria-selected={isCurrent}
                        disabled={Boolean(switching)}
                        onMouseEnter={() => setActiveIndex(idx)}
                        onClick={() => void onSelect(repo.full_name)}
                        className={[
                          "flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left transition-colors duration-100",
                          isActive ? "bg-white/[0.05]" : "hover:bg-white/[0.03]",
                          isCurrent ? "bg-white/[0.03]" : "",
                        ].join(" ")}
                      >
                        <span className="min-w-0 flex-1">
                          <span className="flex items-center gap-1.5">
                            <span className="truncate font-mono text-[12px] tracking-normal text-[#f2f2f2]">
                              {repo.full_name}
                            </span>
                            {repo.private ? (
                              <span className="inline-flex items-center gap-1 text-[10px] text-[#5c5c5c]">
                                <LockIcon />
                                <span>Private</span>
                              </span>
                            ) : (
                              <span className="text-[10px] text-[#4a4a4a]">Public</span>
                            )}
                          </span>
                          <span className="mt-0.5 block text-[10px] text-[#5c5c5c]">
                            {isBusy
                              ? "Switching workspace…"
                              : isCurrent
                                ? "Current workspace"
                                : `Default branch · ${repo.default_branch}`}
                          </span>
                        </span>
                        {isCurrent ? (
                          <span className="shrink-0 rounded-md bg-ok/10 px-1.5 py-0.5 text-[10px] font-medium text-ok">
                            Active
                          </span>
                        ) : isBusy ? (
                          <span className="shrink-0 text-[10px] text-[#8a8a8a]">…</span>
                        ) : null}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          {switchError ? (
            <div className="border-t border-white/[0.06] px-3 py-2 text-[11px] text-danger">
              {switchError}
            </div>
          ) : null}

          <div className="flex items-center justify-between gap-2 border-t border-white/[0.06] px-3 py-2">
            <button
              type="button"
              className="text-[11px] text-[#5c5c5c] transition-colors hover:text-[#a8a8a8]"
              onClick={() => void loadRepos()}
              disabled={list.status === "loading"}
            >
              Refresh list
            </button>
            <Link
              to="/app/settings"
              onClick={() => setOpen(false)}
              className="text-[11px] text-[#8a8a8a] transition-colors hover:text-[#f2f2f2]"
            >
              Manage in Settings →
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
