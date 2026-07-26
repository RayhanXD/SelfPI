import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { api } from "../lib/api";

const titles: Record<string, string> = {
  "/": "Watched APIs",
  "/changes": "Change Feed",
  "/settings": "Settings",
};

function titleFor(pathname: string): string {
  if (pathname.startsWith("/changes/") && pathname.includes("/explorer")) {
    return "Call-Site Explorer";
  }
  if (pathname.startsWith("/changes/")) return "Change Detail";
  return titles[pathname] ?? "SelfPI";
}

export function AppShell() {
  const { pathname } = useLocation();
  const [repo, setRepo] = useState<string | null>(null);
  const wide = pathname.startsWith("/changes/");

  useEffect(() => {
    api
      .listApis()
      .then((apis) => setRepo(apis[0]?.repo ?? null))
      .catch(() => setRepo(null));
  }, []);

  return (
    <div className="flex h-full min-h-0">
      <Sidebar repo={repo} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={titleFor(pathname)} />
        <main className="min-h-0 flex-1 overflow-auto p-6">
          <div className={wide ? "mx-auto w-full max-w-[1400px]" : "mx-auto max-w-[1200px]"}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
