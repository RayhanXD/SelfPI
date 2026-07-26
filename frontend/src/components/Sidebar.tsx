import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "block rounded-md px-3 py-2 text-sm",
    isActive
      ? "bg-surface-3 text-text-primary"
      : "text-text-secondary hover:bg-surface-2 hover:text-text-primary",
  ].join(" ");

interface SidebarProps {
  repo?: string | null;
}

export function Sidebar({ repo }: SidebarProps) {
  return (
    <aside className="flex w-[220px] shrink-0 flex-col border-r border-border bg-surface-1">
      <div className="border-b border-border px-4 py-4">
        <div className="text-lg font-semibold tracking-tight text-text-primary">SelfPI</div>
        <div className="mt-0.5 text-xs text-text-muted">Self-Maintaining APIs</div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 p-2" aria-label="Primary">
        <NavLink to="/" end className={linkClass}>
          Watched APIs
        </NavLink>
        <NavLink to="/changes" className={linkClass}>
          Changes
        </NavLink>
        <NavLink to="/settings" className={linkClass}>
          Settings
        </NavLink>
      </nav>

      <div className="border-t border-border px-4 py-3">
        <div className="text-xs uppercase tracking-wide text-text-muted">Connected repo</div>
        <div className="mt-1 truncate font-mono text-xs text-text-secondary">
          {repo ?? "—"}
        </div>
      </div>
    </aside>
  );
}
