import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { api } from "../lib/api";
import { WorkspaceProvider, useWorkspace } from "../lib/workspace";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

const meta: Record<string, { title: string; description?: string }> = {
  "/app": {
    title: "Dashboard",
    description: "Health of watched APIs and what needs review.",
  },
  "/app/apis": {
    title: "Watched APIs",
    description: "Upstream specs you monitor for breaking changes.",
  },
  "/app/changes": {
    title: "Inbox",
    description: "Detected changes ready for review.",
  },
  "/app/settings": {
    title: "Settings",
    description: "Connect a repo and manage workspace configuration.",
  },
};

function pageMeta(pathname: string) {
  if (pathname.includes("/explorer")) {
    return {
      title: "Call-site explorer",
      description: "Layer, confidence, and IR for every matched site.",
    };
  }
  if (pathname.startsWith("/app/changes/") && pathname !== "/app/changes") {
    return {
      title: "Review change",
      description: "Diff, call sites, and the proposed fix.",
    };
  }
  return meta[pathname] ?? { title: "SelfPI" };
}

function AppShellInner() {
  const { pathname } = useLocation();
  const { title, description } = pageMeta(pathname);
  const { connectedRepo, revision } = useWorkspace();
  const [inboxCount, setInboxCount] = useState(0);
  const isDetail =
    pathname.startsWith("/app/changes/") &&
    pathname !== "/app/changes" &&
    !pathname.includes("/explorer");

  useEffect(() => {
    api
      .listApis()
      .then((apis) => {
        setInboxCount(apis.reduce((n, a) => n + (a.open_change_count ?? 0), 0));
      })
      .catch(() => setInboxCount(0));
  }, [pathname, revision]);

  return (
    <div className="flex h-full min-h-0 bg-[#050505]">
      <Sidebar repo={connectedRepo} inboxCount={inboxCount} />
      <div className="relative flex min-w-0 flex-1 flex-col">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-32 opacity-[0.07]"
          style={{
            background:
              "radial-gradient(80% 80% at 70% -10%, #efc28a 0%, transparent 55%), radial-gradient(60% 70% at 30% -20%, #7aa3c4 0%, transparent 50%)",
          }}
        />
        {!isDetail ? <TopBar title={title} description={description} /> : null}
        <main className="relative min-h-0 flex-1 overflow-auto">
          <div
            className={[
              "mx-auto w-full",
              isDetail ? "max-w-none px-0 py-0" : "max-w-[1120px] px-4 py-7 sm:px-8",
            ].join(" ")}
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

export function AppShell() {
  return (
    <WorkspaceProvider>
      <AppShellInner />
    </WorkspaceProvider>
  );
}
