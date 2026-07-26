type Tone = "ok" | "warn" | "danger" | "info" | "muted";

const toneClass: Record<Tone, string> = {
  ok: "bg-ok",
  warn: "bg-warn",
  danger: "bg-danger",
  info: "bg-info",
  muted: "bg-text-muted",
};

interface StatusPillProps {
  label: string;
  tone: Tone;
}

export function StatusPill({ label, tone }: StatusPillProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-text-secondary">
      <span className={`inline-block size-1.5 rounded-full ${toneClass[tone]}`} aria-hidden />
      <span>{label}</span>
    </span>
  );
}
