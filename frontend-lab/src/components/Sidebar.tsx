import { NavLink, useLocation } from "react-router-dom";
import { mockInboxCount } from "../data/mock";
import { HORIZON_GLOW, HORIZON_SOFT } from "../lib/accents";
import { HorizonUnderline } from "./HorizonUnderline";

function navClass(active: boolean) {
  return [
    "group relative flex items-center rounded-lg px-2.5 py-2 text-[13px] tracking-[-0.01em] transition-colors duration-150 ease-out",
    active
      ? "bg-white/[0.05] text-white"
      : "text-[#8a8a8a] hover:bg-white/[0.03] hover:text-[#c8c8c8]",
  ].join(" ");
}

export function Sidebar() {
  const { pathname } = useLocation();
  const inboxCount = mockInboxCount();
  const onDash = pathname === "/";
  const onInbox = pathname === "/changes";
  const onApis = pathname === "/apis";
  const onSettings = pathname === "/settings";
  const reviewing =
    pathname.startsWith("/changes/") && pathname !== "/changes";

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
            myorg/billing-app
          </div>
        </div>
      </div>

      <nav
        className="flex flex-1 flex-col gap-6 px-2.5 pb-4 pt-2"
        aria-label="Primary"
      >
        <div>
          <div className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#4a4a4a]">
            Workspace
          </div>
          <div className="flex flex-col gap-0.5">
            <NavLink to="/" end className={navClass(onDash)}>
              <HorizonUnderline show={onDash} />
              Dashboard
            </NavLink>
            <NavLink to="/changes" end className={navClass(onInbox)}>
              <HorizonUnderline show={onInbox} />
              Inbox
              {inboxCount > 0 ? (
                <span className="ml-auto rounded-md bg-white/[0.06] px-1.5 py-px font-mono text-[10px] tabular-nums tracking-normal text-[#8a8a8a]">
                  {inboxCount}
                </span>
              ) : null}
            </NavLink>
            <NavLink to="/apis" className={navClass(onApis)}>
              <HorizonUnderline show={onApis} />
              Watched APIs
            </NavLink>
          </div>
        </div>

        <div>
          <div className="mb-2 px-2.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#4a4a4a]">
            Account
          </div>
          <div className="flex flex-col gap-0.5">
            <NavLink to="/settings" className={navClass(onSettings)}>
              <HorizonUnderline show={onSettings} />
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
          <div className="mt-1 truncate font-mono text-[12px] tracking-normal text-[#8a8a8a]">
            {pathname.includes("explorer") ? "Call-site explorer" : "Change detail"}
          </div>
        </div>
      ) : null}
    </aside>
  );
}
