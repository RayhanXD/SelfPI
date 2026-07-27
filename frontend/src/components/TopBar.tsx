import type { ReactNode } from "react";

export function TopBar({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex min-h-[72px] shrink-0 items-center justify-between gap-6 border-b border-white/[0.06] bg-[#050505] px-8">
      <div className="min-w-0 py-4">
        <h1 className="text-[22px] font-semibold tracking-[-0.04em] text-white">
          {title}
        </h1>
        {description ? (
          <p className="mt-1 max-w-xl text-[13px] leading-snug text-[#8a8a8a]">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </header>
  );
}
