import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { api } from "../lib/api";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

const meta: Record<string, { title: string; description?: string }> = {
  "/": {
    title: "Watched APIs",
    description: "Upstream specs you monitor for breaking changes.",
  },
  "/changes": {
    title: "Inbox",
    description: "Detected changes ready for review.",
  },
  "/settings": {
    title: "Settings",
    description: "Workspace connection and runtime configuration.",
  },
};

function pageMeta(pathname: string) {
  if (pathname.includes("/explorer")) {
    return {
      title: "Call-site explorer",
      description: "Layer, confidence, and IR for every matched site.",
    };
  }
  if (pathname.startsWith("/changes/")) {
    return {
      title: "Review change",
      description: "Diff, call sites, and the proposed fix.",
    };
  }
  return meta[pathname] ?? { title: "SelfPI" };
}

export function AppShell() {
  const { pathname } = useLocation();
  const { title, description } = pageMeta(pathname);
  const [repo, setRepo] = useState<string | null>(null);
  const [inboxCount, setInboxCount] = useState(0);
  const isDetail =
    pathname.startsWith("/changes/") && !pathname.includes("/explorer");

  useEffect(() => {
    Promise.all([api.listApis(), api.getSettings()])
      .then(([apis, settings]) => {
        setRepo(settings.connected_repo ?? apis[0]?.repo ?? null);
        setInboxCount(apis.reduce((n, a) => n + (a.open_change_count ?? 0), 0));
      })
      .catch(() => {
        setRepo(null);
        setInboxCount(0);
      });
  }, [pathname]);

  return (
    <div className="flex h-full min-h-0 bg-[#050505]">
      <Sidebar repo={repo} inboxCount={inboxCount} />
      <div className="relative flex min-w-0 flex-1 flex-col">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-32 opacity-[0.07]"
          style={{
            background:
              "radial-gradient(80% 80% at 70% -10%, #efc28a 0%, transparent 55%), radial-gradient(60% 70% at 30% -20%, #7aa3c4 0%, transparent 50%)",
          }}
        />
        {!isDetail ? (
          <TopBar title={title} description={description} />
        ) : null}
        <main className="relative min-h-0 flex-1 overflow-auto">
          <div
            className={[
              "mx-auto w-full",
              isDetail ? "max-w-none px-0 py-0" : "max-w-[1040px] px-8 py-7",
            ].join(" ")}
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
