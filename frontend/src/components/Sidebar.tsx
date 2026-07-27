import { NavLink, useLocation } from "react-router-dom";
import { HORIZON, HORIZON_GLOW, HORIZON_SOFT } from "../lib/accents";
import { useAuth } from "../lib/auth";

function navClass(active: boolean) {
  return [
    "group relative flex items-center rounded-lg px-2.5 py-2 text-[13px] tracking-[-0.01em] transition-colors duration-150 ease-out",
    active
      ? "bg-white/[0.05] text-white"
      : "text-[#8a8a8a] hover:bg-white/[0.03] hover:text-[#c8c8c8]",
  ].join(" ");
}

function Horizon({ show }: { show: boolean }) {
  if (!show) return null;
  return (
    <span
      aria-hidden
      className="absolute inset-x-2.5 bottom-[4px] h-[1.5px] rounded-full"
      style={{ backgroundImage: HORIZON, boxShadow: HORIZON_GLOW }}
    />
  );
}

interface SidebarProps {
  repo?: string | null;
  inboxCount?: number;
}

export function Sidebar({ repo, inboxCount = 0 }: SidebarProps) {
  const { pathname } = useLocation();
  const { user } = useAuth();
  const base = "/app";
  const onDash = pathname === base || pathname === `${base}/`;
  const onInbox = pathname === `${base}/changes`;
  const onApis = pathname === `${base}/apis`;
  const onSettings = pathname === `${base}/settings`;
  const reviewing =
    pathname.startsWith(`${base}/changes/`) && pathname !== `${base}/changes`;

  return (
    <aside className="flex w-[248px] shrink-0 flex-col border-r border-white/[0.06] bg-[#050505]">
      <div className="flex h-[60px] items-center gap-3 px-4">
        <span
          aria-hidden
          className="size-5 rounded-md"
          style={{
            backgroundImage: HORIZON_SOFT,
            boxShadow: `0 0 0 1px rgba(255,255,255,0.1), ${HORIZON_GLOW}`,
          }}
        />
        <div className="min-w-0">
          <div className="text-[14px] font-semibold tracking-[-0.03em] text-white">
            SelfPI
          </div>
          <div className="truncate font-mono text-[10px] tracking-normal text-[#5c5c5c]">
            {repo ?? (user?.login ? `@${user.login}` : "No repo connected")}
          </div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-6 px-2.5 pb-4 pt-2" aria-label="Primary">
        <div>
          <div className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#4a4a4a]">
            Workspace
          </div>
          <div className="flex flex-col gap-0.5">
            <NavLink to={base} end className={navClass(onDash)}>
              <Horizon show={onDash} />
              Dashboard
            </NavLink>
            <NavLink to={`${base}/changes`} end className={navClass(onInbox)}>
              <Horizon show={onInbox} />
              Inbox
              {inboxCount > 0 ? (
                <span className="ml-auto rounded-md bg-white/[0.06] px-1.5 py-px font-mono text-[10px] tabular-nums tracking-normal text-[#8a8a8a]">
                  {inboxCount}
                </span>
              ) : null}
            </NavLink>
            <NavLink to={`${base}/apis`} className={navClass(onApis)}>
              <Horizon show={onApis} />
              Watched APIs
            </NavLink>
          </div>
        </div>

        <div>
          <div className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#4a4a4a]">
            Account
          </div>
          <div className="flex flex-col gap-0.5">
            <NavLink to={`${base}/settings`} className={navClass(onSettings)}>
              <Horizon show={onSettings} />
              Settings
            </NavLink>
          </div>
        </div>
      </nav>

      {reviewing ? (
        <div className="border-t border-white/[0.06] px-4 py-3">
          <div className="text-[10px] uppercase tracking-[0.08em] text-[#4a4a4a]">
            Reviewing
          </div>
          <div className="mt-1 truncate text-[12px] text-[#8a8a8a]">Change detail</div>
        </div>
      ) : null}
    </aside>
  );
}
