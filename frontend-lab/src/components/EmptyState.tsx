export function EmptyState({
  message,
  hint,
}: {
  message: string;
  hint?: string;
}) {
  return (
    <div className="px-1 py-2">
      <p className="text-[13px] tracking-[-0.01em] text-[#5c5c5c]">{message}</p>
      {hint ? (
        <p className="mt-1 text-[12px] leading-relaxed text-[#4a4a4a]">{hint}</p>
      ) : null}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return <p className="text-[13px] text-danger">{message}</p>;
}

export function SkeletonRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-white/[0.07]">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={[
            "flex items-center gap-4 px-5 py-4",
            i > 0 ? "border-t border-white/[0.06]" : "",
          ].join(" ")}
        >
          <div className="h-3 flex-1 animate-pulse rounded-sm bg-white/[0.04]" />
          <div className="h-3 w-20 animate-pulse rounded-sm bg-white/[0.03]" />
          <div className="h-3 w-16 animate-pulse rounded-sm bg-white/[0.03]" />
        </div>
      ))}
    </div>
  );
}

export function Flash({
  tone = "info",
  children,
}: {
  tone?: "ok" | "warn" | "danger" | "info";
  children: string;
}) {
  const toneClass =
    tone === "ok"
      ? "border-[#3ecf8e]/25 bg-[#3ecf8e]/10 text-[#3ecf8e]"
      : tone === "warn"
        ? "border-[#e6b84d]/25 bg-[#e6b84d]/10 text-[#e6b84d]"
        : tone === "danger"
          ? "border-[#f2555a]/25 bg-[#f2555a]/10 text-[#f2555a]"
          : "border-[#7aa3c4]/25 bg-[#7aa3c4]/10 text-[#9bb8d4]";

  return (
    <p
      role="status"
      className={`rounded-lg border px-3 py-2 text-[12px] tracking-[-0.01em] ${toneClass}`}
    >
      {children}
    </p>
  );
}
