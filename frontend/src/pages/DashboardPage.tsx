import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import {
  Panel,
  SectionHeader,
  StatCard,
  TextLink,
} from "../components/DashboardChrome";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import {
  apiStatusLabel,
  apiStatusTone,
  changeStatusLabel,
  changeStatusTone,
} from "../lib/status";
import { useAsync } from "../lib/useAsync";
import type { ChangeStatus } from "../types/api";

export function DashboardPage() {
  const navigate = useNavigate();
  const {
    data: apis,
    error: apisError,
    loading: apisLoading,
    reload: reloadApis,
  } = useAsync(() => api.listApis(), []);
  const {
    data: changes,
    error: changesError,
    loading: changesLoading,
  } = useAsync(() => api.listChanges(), []);
  const {
    data: settings,
    error: settingsError,
    loading: settingsLoading,
  } = useAsync(() => api.getSettings(), []);

  const [busyCheck, setBusyCheck] = useState(false);
  const [checkMsg, setCheckMsg] = useState<string | null>(null);

  const loading = apisLoading || changesLoading || settingsLoading;
  const error = apisError ?? changesError ?? settingsError;

  const stats = useMemo(() => {
    const list = apis ?? [];
    const items = changes?.items ?? [];
    const needsAttention = list.filter(
      (a) => a.status === "breaking_change_unhandled" || a.open_change_count > 0,
    ).length;
    const upToDate = list.filter((a) => a.status === "up_to_date").length;
    const openPrs = items.filter((c) => c.status === "pr_open").length;
    const actionable = items.filter(
      (c) => c.status === "detected" || c.status === "scanning" || c.status === "pr_open",
    );
    return {
      watched: list.length,
      needsAttention,
      upToDate,
      openPrs,
      actionable,
      recent: items.slice(0, 5),
    };
  }, [apis, changes]);

  const connectedRepo =
    settings?.connected_repo ?? apis?.[0]?.repo ?? null;
  const setupSteps = [
    {
      done: Boolean(settings?.github_configured),
      label: "GitHub App configured",
      to: "/app/settings",
    },
    {
      done: Boolean(connectedRepo),
      label: "Repository connected",
      to: "/app/settings",
    },
    {
      done: (apis?.length ?? 0) > 0,
      label: "At least one API watched",
      to: "/app/apis",
    },
  ];
  const setupIncomplete = setupSteps.some((s) => !s.done);

  const onCheckAll = async () => {
    const live = (apis ?? []).filter(
      (a) => a.mode === "live" || (a.mode == null && a.id === "stripe"),
    );
    if (live.length === 0) {
      setCheckMsg("No live APIs to check.");
      return;
    }
    setBusyCheck(true);
    setCheckMsg(null);
    try {
      let total = 0;
      for (const a of live) {
        const r = await api.checkApi(a.id);
        total += r.changes_detected;
      }
      reloadApis();
      if (total > 0) {
        navigate("/app/changes");
      } else {
        setCheckMsg("All live specs checked — no new breaking changes.");
      }
    } catch (e) {
      setCheckMsg(e instanceof Error ? e.message : "Check failed");
    } finally {
      setBusyCheck(false);
    }
  };

  if (error) return <ErrorState message={error} />;
  if (loading || !apis || !changes || !settings) return <SkeletonRows rows={5} cols={4} />;

  return (
    <div className="space-y-8">
      {/* Hero / status */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[12px] font-medium uppercase tracking-[0.1em] text-[#555]">
            Overview
          </p>
          <h2 className="mt-1 text-[24px] font-semibold tracking-[-0.04em] text-white">
            {stats.needsAttention > 0
              ? `${stats.needsAttention} API${stats.needsAttention === 1 ? "" : "s"} need attention`
              : "All watched APIs look healthy"}
          </h2>
          <p className="mt-1.5 max-w-xl text-[13px] text-[#8a8a8a]">
            {connectedRepo
              ? `Monitoring specs for ${connectedRepo}. Review inbox items before they hit production.`
              : "Connect a repository in Settings to open fix PRs automatically."}
          </p>
          {checkMsg ? (
            <p className="mt-2 text-[12px] text-[#a8a8a8]">{checkMsg}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => navigate("/app/changes")}>
            Open inbox
            {stats.actionable.length > 0 ? ` · ${stats.actionable.length}` : ""}
          </Button>
          <Button variant="primary" disabled={busyCheck} onClick={() => void onCheckAll()}>
            {busyCheck ? "Checking…" : "Check live APIs"}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Watched APIs" value={stats.watched} hint="Active monitors" />
        <StatCard
          label="Needs attention"
          value={stats.needsAttention}
          hint="Unhandled or open changes"
          tone={stats.needsAttention > 0 ? "danger" : "ok"}
        />
        <StatCard label="Open PRs" value={stats.openPrs} hint="Awaiting review" />
        <StatCard
          label="Up to date"
          value={stats.upToDate}
          hint="No open breaks"
          tone="ok"
        />
      </div>

      {/* Setup checklist */}
      {setupIncomplete ? (
        <Panel>
          <div className="border-b border-white/[0.06] px-5 py-4">
            <div className="text-[13px] font-semibold tracking-[-0.02em] text-white">
              Finish workspace setup
            </div>
            <p className="mt-1 text-[12px] text-[#8a8a8a]">
              Complete these steps so SelfPI can detect breaks and open PRs.
            </p>
          </div>
          <ul>
            {setupSteps.map((step, i) => (
              <li
                key={step.label}
                className={[
                  "flex items-center gap-3 px-5 py-3.5",
                  i > 0 ? "border-t border-white/[0.06]" : "",
                ].join(" ")}
              >
                <span
                  className={[
                    "flex size-5 items-center justify-center rounded-full text-[11px]",
                    step.done
                      ? "bg-ok/20 text-ok"
                      : "border border-white/[0.12] text-[#5c5c5c]",
                  ].join(" ")}
                  aria-hidden
                >
                  {step.done ? "✓" : i + 1}
                </span>
                <span
                  className={
                    step.done ? "text-[13px] text-[#5c5c5c] line-through" : "text-[13px] text-white"
                  }
                >
                  {step.label}
                </span>
                {!step.done ? (
                  <Link
                    to={step.to}
                    className="ml-auto text-[12px] font-medium text-[#8a8a8a] hover:text-white"
                  >
                    Continue →
                  </Link>
                ) : null}
              </li>
            ))}
          </ul>
        </Panel>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        {/* Needs review */}
        <div>
          <SectionHeader
            title="Needs review"
            action={<TextLink to="/app/changes">View all</TextLink>}
          />
          {stats.actionable.length === 0 ? (
            <Panel className="px-5 py-8">
              <EmptyState message="Nothing waiting — inbox is clear." />
            </Panel>
          ) : (
            <Panel>
              {stats.actionable.slice(0, 6).map((c, idx) => (
                <Link
                  key={c.id}
                  to={`/app/changes/${c.id}`}
                  className={[
                    "block px-5 py-3.5 transition-colors hover:bg-white/[0.025]",
                    idx > 0 ? "border-t border-white/[0.06]" : "",
                  ].join(" ")}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[13px] tracking-normal text-white">
                      {c.operation_id}
                    </span>
                    <StatusPill
                      label={changeStatusLabel(c.status as ChangeStatus)}
                      tone={changeStatusTone(c.status as ChangeStatus)}
                    />
                  </div>
                  <div className="mt-1 flex flex-wrap gap-x-2 font-mono text-[11px] tracking-normal text-[#5c5c5c]">
                    <span>{c.api_id}</span>
                    <span>·</span>
                    <span>{c.kind}</span>
                    <span>·</span>
                    <span className="font-sans text-[#8a8a8a]">
                      {c.call_site_count} site{c.call_site_count === 1 ? "" : "s"}
                    </span>
                  </div>
                </Link>
              ))}
            </Panel>
          )}
        </div>

        {/* Watched snapshot */}
        <div>
          <SectionHeader
            title="Watched APIs"
            action={<TextLink to="/app/apis">Manage</TextLink>}
          />
          {apis.length === 0 ? (
            <Panel className="px-5 py-8">
              <EmptyState message="No APIs configured yet." />
            </Panel>
          ) : (
            <Panel>
              {apis.map((a, idx) => (
                <Link
                  key={a.id}
                  to={`/app/changes?api_id=${a.id}`}
                  className={[
                    "flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-white/[0.025]",
                    idx > 0 ? "border-t border-white/[0.06]" : "",
                  ].join(" ")}
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[13px] font-medium tracking-[-0.02em] text-white">
                      {a.name}
                    </div>
                    <div className="mt-0.5 font-mono text-[11px] tracking-normal text-[#5c5c5c]">
                      {a.current_version ?? "—"}
                    </div>
                  </div>
                  <StatusPill
                    label={apiStatusLabel(a.status)}
                    tone={apiStatusTone(a.status)}
                  />
                </Link>
              ))}
            </Panel>
          )}
        </div>
      </div>

      {/* Recent activity */}
      <div>
        <SectionHeader
          title="Recent activity"
          action={<TextLink to="/app/changes">Inbox</TextLink>}
        />
        {stats.recent.length === 0 ? (
          <Panel className="px-5 py-8">
            <EmptyState message="No changes detected yet. Check a live API or simulate on the demo." />
          </Panel>
        ) : (
          <Panel>
            {stats.recent.map((c, idx) => {
              const tone = changeStatusTone(c.status as ChangeStatus);
              const dot =
                tone === "ok"
                  ? "bg-ok"
                  : tone === "warn"
                    ? "bg-warn"
                    : tone === "danger"
                      ? "bg-danger"
                      : tone === "info"
                        ? "bg-info"
                        : "bg-[#444]";
              return (
              <Link
                key={c.id}
                to={`/app/changes/${c.id}`}
                className={[
                  "flex items-center gap-4 px-5 py-3.5 transition-colors duration-150 hover:bg-white/[0.025]",
                  idx > 0 ? "border-t border-white/[0.06]" : "",
                ].join(" ")}
              >
                <div className={`size-1.5 shrink-0 rounded-full ${dot}`} aria-hidden />
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-[13px] tracking-normal text-white">
                    {c.operation_id}
                  </div>
                  <div className="mt-0.5 text-[12px] text-[#5c5c5c]">
                    {c.api_id} · {c.kind.replace(/_/g, " ")}
                  </div>
                </div>
                <StatusPill
                  label={changeStatusLabel(c.status as ChangeStatus)}
                  tone={tone}
                />
                <time className="hidden shrink-0 font-mono text-[11px] tracking-normal text-[#5c5c5c] sm:block">
                  {c.detected_at?.slice(0, 10) ?? "—"}
                </time>
              </Link>
            );
            })}
          </Panel>
        )}
      </div>
    </div>
  );
}
