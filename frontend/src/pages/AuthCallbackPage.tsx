import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../lib/auth";

/**
 * OAuth return URL — backend redirects here after GitHub callback.
 * Success → /app (or ?next=). Error → /login with reason.
 */
export function AuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { reload } = useAuth();

  useEffect(() => {
    const auth = params.get("auth");
    const reason = params.get("reason") || "login_failed";
    const next = params.get("next") || "/app";

    void (async () => {
      if (auth === "ok") {
        await reload();
        navigate(next.startsWith("/") ? next : "/app", { replace: true });
        return;
      }
      navigate(`/login?error=${encodeURIComponent(reason)}`, { replace: true });
    })();
  }, [params, navigate, reload]);

  return (
    <div className="flex h-full items-center justify-center bg-[#050505]">
      <div className="text-center">
        <p className="text-[14px] font-medium tracking-[-0.02em] text-white">
          Completing sign-in…
        </p>
        <p className="mt-1 text-[12px] text-[#8a8a8a]">Talking to GitHub</p>
      </div>
    </div>
  );
}
