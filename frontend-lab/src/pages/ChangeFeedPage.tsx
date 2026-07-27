import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { StatusPill } from "../components/StatusPill";
import { MOCK_CHANGES } from "../data/mock";
import { HORIZON } from "../lib/accents";
import { changeStatusLabel, changeStatusTone } from "../lib/status";
import type { ChangeStatus } from "../types";

const FILTERS: Array<{ value: string; label: string }> = [
  { value: "", label: "All" },
  { value: "detected", label: "Detected" },
  { value: "pr_open", label: "PR open" },
  { value: "merged", label: "Merged" },
];

export function ChangeFeedPage() {
  const [status, setStatus] = useState("");

  const items = useMemo(
    () => (status ? MOCK_CHANGES.filter((c) => c.status === status) : MOCK_CHANGES),
    [status],
  );

  return (
    <div className="space-y-1">
      <div className="mb-4 flex flex-wrap gap-1 border-b border-white/[0.06] pb-3">
        {FILTERS.map((f) => {
          const active = status === f.value;
          return (
            <button
              key={f.value || "all"}
              type="button"
              onClick={() => setStatus(f.value)}
              className={[
                "relative h-7 rounded-md px-2.5 text-[13px] transition-colors duration-150 ease-out",
                active ? "text-white" : "text-[#666] hover:text-[#aaa]",
              ].join(" ")}
            >
              {f.label}
              {active ? (
                <span
                  aria-hidden
                  className="absolute inset-x-2 -bottom-[13px] h-[2px] rounded-full"
                  style={{ backgroundImage: HORIZON }}
                />
              ) : null}
            </button>
          );
        })}
      </div>

      <div className="divide-y divide-white/[0.06] rounded-xl border border-white/[0.08]">
        {items.map((c) => (
          <Link
            key={c.id}
            to={`/changes/${c.id}`}
            className="group flex items-start gap-3.5 px-4 py-3.5 transition-colors duration-150 ease-out hover:bg-white/[0.02]"
          >
            <div className="mt-[7px] size-[6px] shrink-0 rounded-full bg-[#444] transition-transform duration-150 group-hover:scale-110" />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-[13px] font-medium text-white">
                  {c.operation_id}
                </span>
                <StatusPill
                  label={changeStatusLabel(c.status as ChangeStatus)}
                  tone={changeStatusTone(c.status as ChangeStatus)}
                />
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-x-2 text-[12px] text-[#666]">
                <span className="font-mono">{c.api_id}</span>
                <span>·</span>
                <span className="font-mono">{c.kind}</span>
                <span>·</span>
                <span>
                  {c.call_site_count} site{c.call_site_count === 1 ? "" : "s"}
                </span>
                {c.pr ? (
                  <>
                    <span>·</span>
                    <span className="font-mono">#{c.pr.number}</span>
                  </>
                ) : null}
              </div>
            </div>
            <time className="shrink-0 pt-0.5 font-mono text-[11px] text-[#555]">
              {c.detected_at?.slice(0, 10)}
            </time>
          </Link>
        ))}
      </div>
    </div>
  );
}
