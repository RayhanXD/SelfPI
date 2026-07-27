type Tone = "ok" | "warn" | "danger" | "info" | "muted";

const toneClass: Record<Tone, string> = {
  ok: "bg-ok",
  warn: "bg-warn",
  danger: "bg-danger",
  info: "bg-info",
  muted: "bg-text-faint",
};

export function StatusPill({ label, tone }: { label: string; tone: Tone }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[12px] tracking-[-0.01em] text-[#a8a8a8]">
      <span
        className={`inline-block size-[6px] shrink-0 rounded-full ${toneClass[tone]}`}
        aria-hidden
      />
      <span>{label}</span>
    </span>
  );
}
