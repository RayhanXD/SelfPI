import { useState } from "react";
import { Button } from "../components/Button";
import { Flash } from "../components/EmptyState";
import { MOCK_REPOS, MOCK_USER } from "../data/mock";

export function SettingsPage() {
  const [connected, setConnected] = useState(MOCK_REPOS[0]);
  const [selected, setSelected] = useState(MOCK_REPOS[0]);
  const [signedIn, setSignedIn] = useState(true);
  const [flash, setFlash] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const rows = [
    { label: "GitHub App", value: "Configured" },
    { label: "Default base branch", value: "main" },
    { label: "Connected repo", value: connected ?? "—" },
    { label: "Scheduled watcher", value: "Every 300s" },
    { label: "Primary API", value: "stripe" },
    { label: "Languages", value: "python" },
  ];

  const onConnect = () => {
    setBusy(true);
    window.setTimeout(() => {
      setConnected(selected);
      setFlash(`Connected ${selected}`);
      setBusy(false);
    }, 280);
  };

  const onDisconnect = () => {
    setBusy(true);
    window.setTimeout(() => {
      setConnected("");
      setFlash("Disconnected repo");
      setBusy(false);
    }, 220);
  };

  return (
    <div className="max-w-lg space-y-8">
      {flash ? <Flash tone="info">{flash}</Flash> : null}

      <section className="space-y-3">
        <div>
          <h2 className="text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2]">
            Account
          </h2>
          <p className="mt-1 text-[12px] leading-relaxed text-[#6e6e6e]">
            Sign in with GitHub to connect repositories and open fix PRs.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-white/[0.07] px-5 py-4">
          <div
            aria-hidden
            className="flex h-8 w-8 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.04] font-mono text-[11px] text-[#8a8a8a]"
          >
            {signedIn ? MOCK_USER.login.slice(0, 2).toUpperCase() : "?"}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[13px] text-[#f2f2f2]">
              {signedIn ? MOCK_USER.name : "Not signed in"}
            </div>
            {signedIn ? (
              <div className="font-mono text-[11px] tracking-normal text-[#6e6e6e]">
                @{MOCK_USER.login}
              </div>
            ) : (
              <div className="text-[11px] text-[#5c5c5c]">Lab mock session</div>
            )}
          </div>
          {signedIn ? (
            <Button
              variant="ghost"
              onClick={() => {
                setSignedIn(false);
                setFlash("Signed out (lab mock).");
              }}
            >
              Sign out
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={() => {
                setSignedIn(true);
                setFlash("Signed in with GitHub (lab mock).");
              }}
            >
              Login with GitHub
            </Button>
          )}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2]">
          Workspace
        </h2>
        <div className="overflow-hidden rounded-2xl border border-white/[0.07]">
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
                {row.value || "—"}
              </dd>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2]">
            Connect repository
          </h2>
          <p className="mt-1 text-[12px] leading-relaxed text-[#6e6e6e]">
            Pick a repo the GitHub App can access. SelfPI opens fix PRs here.
          </p>
        </div>

        {!signedIn ? (
          <div className="rounded-2xl border border-white/[0.07] px-5 py-4 text-[12px] leading-relaxed text-[#6e6e6e]">
            Sign in with GitHub to list and connect repositories.
          </div>
        ) : (
          <div className="space-y-3 rounded-2xl border border-white/[0.07] px-5 py-4">
            <label className="block space-y-1.5">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#5c5c5c]">
                Repository
              </span>
              <select
                className="h-9 w-full rounded-lg border border-[#2e2e2e] bg-[#0a0a0a] px-3 font-mono text-[12px] tracking-normal text-[#f2f2f2] outline-none transition-colors focus:border-[#4a4a4a]"
                value={selected}
                onChange={(e) => setSelected(e.target.value)}
                disabled={busy}
              >
                {MOCK_REPOS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                    {r === connected ? " · connected" : ""}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="primary"
                disabled={busy || !selected || selected === connected}
                onClick={onConnect}
              >
                {busy ? "Saving…" : "Connect repo"}
              </Button>
              {connected ? (
                <Button variant="ghost" disabled={busy} onClick={onDisconnect}>
                  Disconnect
                </Button>
              ) : null}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
