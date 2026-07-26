import { confidenceTone } from "../lib/status";

const fillClass = {
  ok: "bg-ok",
  warn: "bg-warn",
  danger: "bg-danger",
} as const;

interface ConfidenceBarProps {
  value: number;
}

export function ConfidenceBar({ value }: ConfidenceBarProps) {
  const tone = confidenceTone(value);
  const pct = Math.round(Math.min(1, Math.max(0, value)) * 100);

  return (
    <span className="inline-flex items-center gap-2 min-w-[7rem]">
      <span className="relative h-1 w-16 overflow-hidden rounded-sm bg-surface-3">
        <span
          className={`absolute inset-y-0 left-0 ${fillClass[tone]}`}
          style={{ width: `${pct}%` }}
        />
      </span>
      <span className="font-mono text-xs text-text-secondary tabular-nums">
        {value.toFixed(2)}
      </span>
    </span>
  );
}
