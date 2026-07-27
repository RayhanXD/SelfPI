import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { FilterChips } from "../components/FilterChips";
import { StatusPill } from "../components/StatusPill";
import { MOCK_CHANGES } from "../data/mock";
import { changeStatusLabel, changeStatusTone } from "../lib/status";
import type { ChangeStatus } from "../types";

const FILTERS: Array<{ value: ChangeStatus | ""; label: string }> = [
  { value: "", label: "All" },
  { value: "detected", label: "Detected" },
  { value: "scanning", label: "Scanning" },
  { value: "pr_open", label: "PR open" },
  { value: "merged", label: "Merged" },
  { value: "dismissed", label: "Dismissed" },
];

export function ChangeFeedPage() {
  const [params, setParams] = useSearchParams();
  const apiId = params.get("api_id") ?? "";
  const status = (params.get("status") ?? "") as ChangeStatus | "";

  const items = useMemo(() => {
    return MOCK_CHANGES.filter((c) => {
      if (apiId && c.api_id !== apiId) return false;
      if (status && c.status !== status) return false;
      return true;
    });
  }, [apiId, status]);

  const setStatus = (next: ChangeStatus | "") => {
    const p = new URLSearchParams(params);
    if (next) p.set("status", next);
    else p.delete("status");
    setParams(p, { replace: true });
  };

  const clearApi = () => {
    const p = new URLSearchParams(params);
    p.delete("api_id");
    setParams(p, { replace: true });
  };

  return (
    <div>
      <FilterChips options={FILTERS} value={status} onChange={setStatus} />

      {apiId ? (
        <div className="mb-4 inline-flex items-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.02] px-2.5 py-1.5">
          <span className="text-[11px] uppercase tracking-[0.08em] text-[#5c5c5c]">
            API
          </span>
          <span className="font-mono text-[12px] tracking-normal text-[#a8a8a8]">
            {apiId}
          </span>
          <button
            type="button"
            onClick={clearApi}
            className="ml-1 text-[12px] text-[#666] transition-colors hover:text-white"
            aria-label="Clear API filter"
          >
            ×
          </button>
        </div>
      ) : null}

      {items.length === 0 ? (
        <div className="rounded-2xl border border-white/[0.07] px-5 py-10">
          <EmptyState
            message="No changes match this filter."
            hint="Try All, or clear the API filter if one is set."
          />
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-white/[0.07]">
          {items.map((c, idx) => (
            <Link
              key={c.id}
              to={`/changes/${c.id}`}
              className={[
                "group flex items-start gap-3.5 px-5 py-4 transition-colors duration-150 ease-out hover:bg-white/[0.025]",
                idx > 0 ? "border-t border-white/[0.06]" : "",
              ].join(" ")}
            >
              <span
                className={[
                  "mt-[7px] size-[6px] shrink-0 rounded-full",
                  changeStatusTone(c.status as ChangeStatus) === "ok"
                    ? "bg-ok"
                    : changeStatusTone(c.status as ChangeStatus) === "warn"
                      ? "bg-warn"
                      : changeStatusTone(c.status as ChangeStatus) === "danger"
                        ? "bg-danger"
                        : changeStatusTone(c.status as ChangeStatus) === "info"
                          ? "bg-info"
                          : "bg-[#444]",
                ].join(" ")}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[13px] font-medium tracking-normal text-white">
                    {c.operation_id}
                  </span>
                  <StatusPill
                    label={changeStatusLabel(c.status as ChangeStatus)}
                    tone={changeStatusTone(c.status as ChangeStatus)}
                  />
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-x-2 text-[12px] text-[#666]">
                  <span className="font-mono tracking-normal">{c.api_id}</span>
                  <span className="text-[#3a3a3a]">·</span>
                  <span className="font-mono tracking-normal">{c.kind}</span>
                  <span className="text-[#3a3a3a]">·</span>
                  <span>
                    {c.call_site_count} site{c.call_site_count === 1 ? "" : "s"}
                  </span>
                  {c.pr ? (
                    <>
                      <span className="text-[#3a3a3a]">·</span>
                      <span className="font-mono tracking-normal">#{c.pr.number}</span>
                    </>
                  ) : null}
                </div>
              </div>
              <time className="shrink-0 pt-0.5 font-mono text-[11px] tracking-normal text-[#5c5c5c]">
                {c.detected_at?.slice(0, 10) ?? "—"}
              </time>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
