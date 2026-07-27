import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function SectionHeader({
  title,
  action,
}: {
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <h2 className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#555]">
        {title}
      </h2>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "warn" | "ok" | "danger";
}) {
  const valueClass =
    tone === "warn"
      ? "text-warn"
      : tone === "ok"
        ? "text-ok"
        : tone === "danger"
          ? "text-danger"
          : "text-white";

  return (
    <div className="rounded-2xl border border-white/[0.07] bg-[#0a0a0a] px-4 py-4">
      <div className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#555]">
        {label}
      </div>
      <div className={`mt-2 text-[28px] font-semibold tracking-[-0.04em] ${valueClass}`}>
        {value}
      </div>
      {hint ? <div className="mt-1 text-[12px] text-[#5c5c5c]">{hint}</div> : null}
    </div>
  );
}

export function Panel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={[
        "overflow-hidden rounded-2xl border border-white/[0.07] bg-[#0a0a0a]",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}

export function TextLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="text-[12px] font-medium text-[#8a8a8a] transition-colors hover:text-white"
    >
      {children}
    </Link>
  );
}
