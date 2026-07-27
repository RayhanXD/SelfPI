import { confidenceTone } from "../lib/status";

export function ConfidenceBar({ value }: { value: number }) {
  const tone = confidenceTone(value);
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100);
  const fill =
    tone === "ok" ? "bg-ok" : tone === "warn" ? "bg-warn" : "bg-danger";

  return (
    <span className="inline-flex min-w-[6.5rem] items-center gap-2">
      <span className="relative h-px w-12 overflow-visible bg-border-strong">
        <span
          className={`absolute left-0 top-1/2 h-[3px] -translate-y-1/2 rounded-full ${fill}`}
          style={{ width: `${pct}%` }}
        />
      </span>
      <span className="font-mono text-[11px] tabular-nums text-text-faint">
        {value.toFixed(2)}
      </span>
    </span>
  );
}
