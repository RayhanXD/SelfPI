import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import {
  Panel,
  SectionHeader,
  StatCard,
  TextLink,
} from "../components/DashboardChrome";
import { EmptyState } from "../components/EmptyState";
import { StatusPill } from "../components/StatusPill";
import { MOCK_APIS, MOCK_CHANGES } from "../data/mock";
import { HORIZON, HORIZON_GLOW } from "../lib/accents";
import {
  apiStatusLabel,
  apiStatusTone,
  changeStatusLabel,
  changeStatusTone,
} from "../lib/status";
import type { ChangeStatus } from "../types";

export function DashboardPage() {
  const navigate = useNavigate();
  const apis = MOCK_APIS;
  const items = MOCK_CHANGES;

  const needsAttention = apis.filter(
    (a) => a.status === "breaking_change_unhandled" || a.open_change_count > 0,
  ).length;
  const upToDate = apis.filter((a) => a.status === "up_to_date").length;
  const openPrs = items.filter((c) => c.status === "pr_open").length;
  const actionable = items.filter(
    (c) => c.status === "detected" || c.status === "scanning" || c.status === "pr_open",
  );
  const recent = items.slice(0, 5);
  const connectedRepo = apis[0]?.repo ?? "myorg/billing-app";

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[12px] font-medium uppercase tracking-[0.1em] text-[#555]">
            Overview
          </p>
          <h2 className="mt-1 text-[24px] font-semibold tracking-[-0.04em] text-white">
            {needsAttention > 0
              ? `${needsAttention} API${needsAttention === 1 ? "" : "s"} need attention`
              : "All watched APIs look healthy"}
          </h2>
          <p className="mt-1.5 max-w-xl text-[13px] text-[#8a8a8a]">
            Monitoring specs for {connectedRepo}. Review inbox items before they hit
            production.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => navigate("/changes")}>
            Open inbox · {actionable.length}
          </Button>
          <Button variant="primary" onClick={() => navigate("/apis")}>
            Check live APIs
          </Button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Watched APIs" value={apis.length} hint="Active monitors" />
        <StatCard
          label="Needs attention"
          value={needsAttention}
          hint="Unhandled or open changes"
          tone={needsAttention > 0 ? "danger" : "ok"}
        />
        <StatCard label="Open PRs" value={openPrs} hint="Awaiting review" />
        <StatCard label="Up to date" value={upToDate} hint="No open breaks" tone="ok" />
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <div>
          <SectionHeader
            title="Needs review"
            action={<TextLink to="/changes">View all</TextLink>}
          />
          {actionable.length === 0 ? (
            <Panel className="px-5 py-8">
              <EmptyState message="Nothing waiting — inbox is clear." />
            </Panel>
          ) : (
            <Panel>
              {actionable.map((c, idx) => (
                <Link
                  key={c.id}
                  to={`/changes/${c.id}`}
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

        <div>
          <SectionHeader
            title="Watched APIs"
            action={<TextLink to="/apis">Manage</TextLink>}
          />
          <Panel>
            {apis.map((a, idx) => (
              <Link
                key={a.id}
                to="/changes"
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
        </div>
      </div>

      <div>
        <SectionHeader title="Recent activity" action={<TextLink to="/changes">Inbox</TextLink>} />
        <Panel>
          {recent.map((c, idx) => (
            <Link
              key={c.id}
              to={`/changes/${c.id}`}
              className={[
                "flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-white/[0.025]",
                idx > 0 ? "border-t border-white/[0.06]" : "",
              ].join(" ")}
            >
              <div
                className="size-1.5 shrink-0 rounded-full bg-[#444]"
                style={
                  c.status === "detected" || c.status === "pr_open"
                    ? { backgroundImage: HORIZON, boxShadow: HORIZON_GLOW }
                    : undefined
                }
                aria-hidden
              />
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
                tone={changeStatusTone(c.status as ChangeStatus)}
              />
              <time className="hidden shrink-0 font-mono text-[11px] tracking-normal text-[#5c5c5c] sm:block">
                {c.detected_at?.slice(0, 10) ?? "—"}
              </time>
            </Link>
          ))}
        </Panel>
      </div>
    </div>
  );
}
