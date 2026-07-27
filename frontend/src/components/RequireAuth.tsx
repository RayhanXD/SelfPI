import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth";

export function RequireAuth() {
  const { loading, authenticated, loginRequired } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-[#050505]">
        <div className="text-[13px] text-[#8a8a8a]">Loading workspace…</div>
      </div>
    );
  }

  if (loginRequired && !authenticated) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  return <Outlet />;
}
