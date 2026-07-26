import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

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

  return (
    <div className="flex h-full min-h-0">
      <Sidebar repo="myorg/billing-app" />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar title={titleFor(pathname)} />
        <main className="min-h-0 flex-1 overflow-auto p-6">
          <div className="mx-auto max-w-[1200px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
