import { useEffect, useRef } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { BrandMark } from "../components/BrandMark";
import { GitHubMark } from "../components/GitHubMark";
import { HORIZON, HORIZON_GLOW } from "../lib/accents";
import { sanitizeNextPath } from "../lib/api";
import { useAuth } from "../lib/auth";

const ERROR_COPY: Record<string, string> = {
  oauth_not_configured: "GitHub OAuth isn’t configured on this server yet.",
  login_failed: "GitHub login failed. Try again.",
  missing_code: "GitHub didn’t return an auth code.",
  bad_state: "Login session expired. Start again.",
  token_exchange_failed: "Couldn’t exchange the GitHub code for a session.",
  install_needs_login: "Sign in with GitHub to finish installing the App.",
};

export function LoginPage() {
  const { loading, authenticated, oauthConfigured, loginHrefFor } = useAuth();
  const [params] = useSearchParams();
  const next = sanitizeNextPath(params.get("next"), "/app");
  const errorKey = params.get("error") || params.get("reason") || "";
  const errorMsg = errorKey
    ? ERROR_COPY[errorKey] ?? `Sign-in failed (${errorKey}).`
    : null;
  const loginHref = loginHrefFor(next);
  const autoStarted = useRef(false);

  // No error → start GitHub OAuth immediately (one click from landing / RequireAuth).
  useEffect(() => {
    if (loading || authenticated || errorMsg || !oauthConfigured) return;
    if (autoStarted.current) return;
    autoStarted.current = true;
    window.location.assign(loginHref);
  }, [loading, authenticated, errorMsg, oauthConfigured, loginHref]);

  if (!loading && authenticated) {
    return <Navigate to={next} replace />;
  }

  const startingOAuth = !loading && !errorMsg && oauthConfigured;

  return (
    <div className="relative flex min-h-full flex-col bg-[#050505]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-72 opacity-80"
        style={{
          background: `
            radial-gradient(50% 60% at 50% -10%, rgba(232,160,122,0.2) 0%, transparent 60%),
            radial-gradient(40% 50% at 80% 10%, rgba(122,163,196,0.14) 0%, transparent 55%)
          `,
        }}
      />

      <header className="relative z-10 px-6 py-5 md:px-8">
        <Link to="/" className="inline-flex items-center gap-2.5">
          <BrandMark size={20} />
          <span className="text-[15px] font-semibold tracking-[-0.03em] text-white">
            SelfPI
          </span>
        </Link>
      </header>

      <main className="relative z-10 flex flex-1 items-center justify-center px-6 pb-16">
        <div className="w-full max-w-[400px]">
          <div className="mb-8 text-center">
            <h1 className="text-[28px] font-semibold tracking-[-0.04em] text-white">
              Sign in
            </h1>
            <p className="mt-2 text-[14px] leading-relaxed text-[#8a8a8a]">
              Connect with GitHub to watch specs and open fix PRs on your repos.
            </p>
          </div>

          <div className="rounded-2xl border border-white/[0.08] bg-[#0a0a0a] p-6">
            {errorMsg ? (
              <p className="mb-4 rounded-lg border border-[#f2555a]/25 bg-[#f2555a]/10 px-3 py-2 text-[12px] text-[#f2555a]">
                {errorMsg}
              </p>
            ) : null}

            {loading || startingOAuth ? (
              <p className="text-center text-[13px] text-[#8a8a8a]">
                {startingOAuth ? "Redirecting to GitHub…" : "Checking session…"}
              </p>
            ) : oauthConfigured ? (
              <a
                href={loginHref}
                className="inline-flex h-11 w-full items-center justify-center gap-2.5 rounded-lg bg-white text-[14px] font-medium text-[#0a0a0a] transition-[background-color,transform] duration-150 hover:bg-[#ebebeb] active:scale-[0.98]"
              >
                <GitHubMark className="size-4" />
                Continue with GitHub
              </a>
            ) : (
              <div className="space-y-3 text-center">
                <p className="text-[13px] text-[#8a8a8a]">
                  OAuth isn’t configured. Set{" "}
                  <span className="font-mono text-[#a8a8a8]">GITHUB_CLIENT_ID</span> and{" "}
                  <span className="font-mono text-[#a8a8a8]">GITHUB_CLIENT_SECRET</span>{" "}
                  in the backend, then reload.
                </p>
                <Link
                  to="/app"
                  className="inline-flex h-10 w-full items-center justify-center rounded-lg border border-[#2e2e2e] text-[13px] font-medium text-[#f2f2f2] transition-colors hover:bg-white/[0.04]"
                >
                  Continue without login (dev)
                </Link>
              </div>
            )}

            <div
              aria-hidden
              className="mx-auto mt-6 h-[2px] w-16 rounded-full"
              style={{ backgroundImage: HORIZON, boxShadow: HORIZON_GLOW }}
            />
            <p className="mt-4 text-center text-[12px] leading-relaxed text-[#5c5c5c]">
              We’ll only use your GitHub identity to connect repos the App can
              access. No password stored.
            </p>
          </div>

          <p className="mt-6 text-center text-[12px] text-[#5c5c5c]">
            <Link to="/" className="text-[#8a8a8a] transition-colors hover:text-white">
              ← Back to SelfPI
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
