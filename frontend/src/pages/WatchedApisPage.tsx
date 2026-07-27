import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { EmptyState, ErrorState, Flash, SkeletonRows } from "../components/EmptyState";
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
  const [notice, setNotice] = useState<string | null>(null);

  const onCheck = async (id: string) => {
    setBusy(`check:${id}`);
    setActionError(null);
    setNotice(null);
    try {
      const result = await api.checkApi(id);
      reload();
      if (result.changes_detected > 0) {
        navigate(`/app/changes?api_id=${id}`);
      } else {
        setNotice("Check complete — no new breaking changes.");
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
    setNotice(null);
    try {
      const version = `demo-${Date.now()}`;
      const result = await api.pushSpecVersion(id, version, {
        ...DEMO_BUMP_SPEC,
        info: { ...DEMO_BUMP_SPEC.info, version },
      });
      reload();
      if (result.changes_detected > 0) {
        navigate(`/app/changes?api_id=${id}`);
      } else {
        setNotice(
          "Bump stored, but no new diff. Open Changes, or run make reset then bump once.",
        );
        navigate(`/app/changes?api_id=${id}`);
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Bump failed");
    } finally {
      setBusy(null);
    }
  };

  if (error) return <ErrorState message={error} />;
  if (loading || !apis) return <SkeletonRows />;
  if (apis.length === 0) {
    return (
      <div className="rounded-2xl border border-white/[0.07] px-5 py-10">
        <EmptyState
          message="No APIs watched yet."
          hint="Connect a repository in Settings to detect APIs."
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-[12px] leading-relaxed text-[#6e6e6e]">
        <span className="font-mono text-[#8a8a8a]">Bump spec</span> is demo-only
        (source → payment_method).{" "}
        <span className="font-mono text-[#8a8a8a]">Check now</span> polls the live
        OpenAPI. After the first successful bump, run{" "}
        <span className="font-mono text-[#8a8a8a]">make reset</span> to bump again.
      </p>
      {notice ? <Flash tone="info">{notice}</Flash> : null}
      {actionError ? <Flash tone="danger">{actionError}</Flash> : null}

      <div className="overflow-hidden rounded-2xl border border-white/[0.07]">
        {apis.map((a, idx) => (
          <div
            key={a.id}
            className={[
              "group flex flex-wrap items-center gap-4 px-5 py-4 transition-colors duration-150 ease-out hover:bg-white/[0.025]",
              idx > 0 ? "border-t border-white/[0.06]" : "",
            ].join(" ")}
          >
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2.5">
                <Link
                  to={`/app/changes?api_id=${a.id}`}
                  className="text-[15px] font-semibold tracking-[-0.03em] text-white transition-opacity hover:opacity-80"
                >
                  {a.name}
                </Link>
                <StatusPill
                  label={apiStatusLabel(a.status)}
                  tone={apiStatusTone(a.status)}
                />
                {isDemoApi(a) ? (
                  <span className="rounded-md border border-white/[0.08] px-1.5 py-px text-[10px] font-medium uppercase tracking-[0.08em] text-[#5c5c5c]">
                    Demo
                  </span>
                ) : null}
              </div>
              <div className="mt-1.5 flex flex-wrap items-center gap-x-2 font-mono text-[11px] tracking-normal text-[#5c5c5c]">
                <span>{a.id}</span>
                <span className="text-[#3a3a3a]">·</span>
                <span>{a.current_version ?? "—"}</span>
                <span className="text-[#3a3a3a]">·</span>
                <span className="font-sans tracking-[-0.01em] text-[#8a8a8a]">
                  {a.open_change_count} open change
                  {a.open_change_count === 1 ? "" : "s"}
                </span>
                {a.last_checked ? (
                  <>
                    <span className="text-[#3a3a3a]">·</span>
                    <span className="font-sans text-[#5c5c5c]">
                      checked {a.last_checked.slice(0, 16).replace("T", " ")}
                    </span>
                  </>
                ) : null}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {a.open_change_count > 0 ? (
                <Link
                  to={`/app/changes?api_id=${a.id}`}
                  className="inline-flex h-8 items-center rounded-lg px-2.5 text-[12px] font-medium text-[#8a8a8a] transition-colors hover:bg-white/[0.04] hover:text-white"
                >
                  View inbox
                </Link>
              ) : null}
              {isDemoApi(a) ? (
                <Button
                  variant="primary"
                  disabled={busy === `bump:${a.id}`}
                  onClick={() => void onBump(a.id)}
                >
                  {busy === `bump:${a.id}` ? "Bumping…" : "Simulate change"}
                </Button>
              ) : null}
              {isLiveApi(a) ? (
                <Button
                  variant="secondary"
                  disabled={busy === `check:${a.id}`}
                  onClick={() => void onCheck(a.id)}
                >
                  {busy === `check:${a.id}` ? "Checking…" : "Check now"}
                </Button>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
