import type { ReactNode } from "react";
import { RepoSwitcher } from "./RepoSwitcher";

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
    <header className="flex min-h-[72px] shrink-0 items-center justify-between gap-4 border-b border-white/[0.06] bg-[#050505] px-4 sm:gap-6 sm:px-8">
      <div className="min-w-0 py-4">
        <h1 className="text-[18px] font-semibold tracking-[-0.04em] text-white sm:text-[22px]">
          {title}
        </h1>
        {description ? (
          <p className="mt-1 max-w-xl truncate text-[12px] leading-snug text-[#8a8a8a] sm:text-[13px] sm:whitespace-normal">
            {description}
          </p>
        ) : null}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {actions}
        <RepoSwitcher />
      </div>
    </header>
  );
}
