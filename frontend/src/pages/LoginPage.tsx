import { Link, Navigate, useSearchParams } from "react-router-dom";
import { HORIZON, HORIZON_GLOW, HORIZON_SOFT } from "../lib/accents";
import { useAuth } from "../lib/auth";

function GitHubMark({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor" aria-hidden>
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

const ERROR_COPY: Record<string, string> = {
  oauth_not_configured: "GitHub OAuth isn’t configured on this server yet.",
  login_failed: "GitHub login failed. Try again.",
  missing_code: "GitHub didn’t return an auth code.",
  bad_state: "Login session expired. Start again.",
  token_exchange_failed: "Couldn’t exchange the GitHub code for a session.",
};

export function LoginPage() {
  const { loading, authenticated, oauthConfigured, loginUrl } = useAuth();
  const [params] = useSearchParams();
  const next = params.get("next") || "/app";
  const errorKey = params.get("error") || params.get("reason") || "";
  const errorMsg = errorKey
    ? ERROR_COPY[errorKey] ?? `Sign-in failed (${errorKey}).`
    : null;

  if (!loading && authenticated) {
    return <Navigate to={next.startsWith("/") ? next : "/app"} replace />;
  }

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
          <span
            aria-hidden
            className="size-5 rounded-md"
            style={{
              backgroundImage: HORIZON_SOFT,
              boxShadow: `0 0 0 1px rgba(255,255,255,0.1), ${HORIZON_GLOW}`,
            }}
          />
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

            {loading ? (
              <p className="text-center text-[13px] text-[#8a8a8a]">Checking session…</p>
            ) : oauthConfigured || loginUrl ? (
              <a
                href={loginUrl ?? "/auth/github/login"}
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
