import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { BrandMark } from "../components/BrandMark";
import { api, sanitizeNextPath } from "../lib/api";
import { useAuth } from "../lib/auth";

/**
 * OAuth return URL — backend redirects here after GitHub callback.
 * Prefers one-time `handoff` exchange (works when cross-site cookies are blocked),
 * then falls back to cookie session reload. Success → /app (or ?next=).
 */
export function AuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { reload, applySession } = useAuth();
  const [status, setStatus] = useState("Completing sign-in…");
  const ran = useRef(false);

  useEffect(() => {
    if (ran.current) return;
    ran.current = true;

    const auth = params.get("auth");
    const reason = params.get("reason") || "login_failed";
    const next = sanitizeNextPath(params.get("next"), "/app");
    const handoff = params.get("handoff");

    // Drop secrets from the address bar ASAP.
    if (handoff || auth) {
      const clean = new URL(window.location.href);
      clean.searchParams.delete("handoff");
      window.history.replaceState({}, "", `${clean.pathname}${clean.search}`);
    }

    void (async () => {
      if (auth !== "ok") {
        navigate(`/login?error=${encodeURIComponent(reason)}&next=${encodeURIComponent(next)}`, {
          replace: true,
        });
        return;
      }

      try {
        if (handoff) {
          setStatus("Confirming session…");
          const data = await api.completeHandoff(handoff);
          applySession(data, data.session_token);
          setStatus("Signed in — opening workspace…");
          navigate(next, { replace: true });
          return;
        }

        // Legacy / cookie-only path
        for (let attempt = 0; attempt < 6; attempt++) {
          if (attempt > 0) {
            setStatus("Confirming session…");
            await new Promise((r) => setTimeout(r, 250 * attempt));
          }
          const me = await reload();
          if (me?.authenticated) {
            setStatus("Signed in — opening workspace…");
            navigate(next, { replace: true });
            return;
          }
        }
      } catch {
        /* fall through to error */
      }

      navigate(`/login?error=login_failed&next=${encodeURIComponent(next)}`, {
        replace: true,
      });
    })();
  }, [params, navigate, reload, applySession]);

  return (
    <div className="flex h-full flex-col items-center justify-center bg-[#050505]">
      <BrandMark size={28} className="mb-6 opacity-90" />
      <div className="text-center">
        <p className="text-[14px] font-medium tracking-[-0.02em] text-white">{status}</p>
        <p className="mt-1 text-[12px] text-[#8a8a8a]">Talking to GitHub</p>
        <div
          aria-hidden
          className="mx-auto mt-5 h-1 w-24 overflow-hidden rounded-full bg-white/[0.06]"
        >
          <div className="h-full w-1/2 animate-pulse rounded-full bg-white/40" />
        </div>
      </div>
    </div>
  );
}
