import { Link } from "react-router-dom";
import { Button } from "../components/Button";
import { StatusPill } from "../components/StatusPill";
import { MOCK_APIS } from "../data/mock";
import { apiStatusLabel, apiStatusTone } from "../lib/status";

export function WatchedApisPage() {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.07]">
      {MOCK_APIS.map((a, idx) => (
        <div
          key={a.id}
          className={[
            "group flex items-center gap-4 px-5 py-4 transition-colors duration-150 ease-out hover:bg-white/[0.025]",
            idx > 0 ? "border-t border-white/[0.06]" : "",
          ].join(" ")}
        >
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <Link
                to="/changes"
                className="text-[15px] font-semibold tracking-[-0.03em] text-white transition-opacity hover:opacity-80"
              >
                {a.name}
              </Link>
              <StatusPill label={apiStatusLabel(a.status)} tone={apiStatusTone(a.status)} />
              {a.mode === "demo" ? (
                <span className="rounded-md border border-white/[0.08] px-1.5 py-px text-[10px] font-medium uppercase tracking-[0.08em] text-[#5c5c5c]">
                  Demo
                </span>
              ) : null}
            </div>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-2 font-mono text-[11px] tracking-normal text-[#5c5c5c]">
              <span>{a.id}</span>
              <span className="text-[#3a3a3a]">·</span>
              <span>{a.current_version}</span>
              <span className="text-[#3a3a3a]">·</span>
              <span className="font-sans tracking-[-0.01em] text-[#8a8a8a]">
                {a.open_change_count} open change{a.open_change_count === 1 ? "" : "s"}
              </span>
            </div>
          </div>
          <div className="shrink-0 opacity-85 transition-opacity group-hover:opacity-100">
            {a.mode === "demo" ? (
              <Button variant="primary">Simulate change</Button>
            ) : (
              <Button variant="secondary">Check now</Button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
