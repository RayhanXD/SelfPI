import { Link } from "react-router-dom";
import { BrandMark } from "../components/BrandMark";
import { HORIZON, HORIZON_GLOW } from "../lib/accents";
import { resolveApiUrl } from "../lib/api";
import { useAuth } from "../lib/auth";

function GitHubMark({ className = "" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor" aria-hidden>
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

export function LandingPage() {
  const { authenticated, loading } = useAuth();
  const primaryTo = !loading && authenticated ? "/app" : "/login";
  const primaryLabel = !loading && authenticated ? "Open workspace" : "Get started";

  return (
    <div className="relative min-h-full overflow-hidden bg-[#050505] text-[#f2f2f2]">
      <div
        aria-hidden
        className="animate-horizon pointer-events-none absolute inset-x-0 top-0 h-[70vh]"
        style={{
          background: `
            radial-gradient(55% 45% at 70% -5%, rgba(232,160,122,0.22) 0%, transparent 55%),
            radial-gradient(40% 35% at 25% 0%, rgba(122,163,196,0.18) 0%, transparent 50%),
            linear-gradient(180deg, #0a0a0a 0%, #050505 70%)
          `,
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-[42%] h-px opacity-80"
        style={{ backgroundImage: HORIZON, boxShadow: HORIZON_GLOW }}
      />

      <header className="relative z-10 mx-auto flex w-full max-w-[1120px] items-center justify-between px-6 py-5 md:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <BrandMark size={20} />
          <span className="text-[15px] font-semibold tracking-[-0.03em]">SelfPI</span>
        </Link>
        <div className="flex items-center gap-2">
          {authenticated ? (
            <Link
              to="/app"
              className="inline-flex h-8 items-center rounded-lg bg-white px-3 text-[13px] font-medium text-[#0a0a0a] transition-[background-color,transform] duration-150 hover:bg-[#ebebeb] active:scale-[0.98]"
            >
              Open workspace
            </Link>
          ) : (
            <>
              <Link
                to="/login"
                className="inline-flex h-8 items-center rounded-lg px-3 text-[13px] font-medium text-[#8a8a8a] transition-colors hover:text-white"
              >
                Sign in
              </Link>
              <Link
                to="/login"
                className="inline-flex h-8 items-center rounded-lg bg-white px-3 text-[13px] font-medium text-[#0a0a0a] transition-[background-color,transform] duration-150 hover:bg-[#ebebeb] active:scale-[0.98]"
              >
                Get started
              </Link>
            </>
          )}
        </div>
      </header>

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-72px)] w-full max-w-[1120px] flex-col justify-center px-6 pb-16 pt-10 md:px-8">
        <div className="max-w-[640px]">
          <p className="animate-fade-up text-[11px] font-semibold uppercase tracking-[0.14em] text-[#5c5c5c]">
            Self-maintaining APIs
          </p>
          <h1 className="animate-fade-up-delay mt-4 text-[clamp(2.4rem,6vw,3.75rem)] font-semibold leading-[1.05] tracking-[-0.045em] text-white">
            SelfPI
          </h1>
          <p className="animate-fade-up-delay mt-4 max-w-md text-[17px] leading-relaxed tracking-[-0.02em] text-[#a8a8a8]">
            Watch upstream specs. Find every broken call site. Open the fix PR
            before production notices.
          </p>
          <div className="animate-fade-up-delay-2 mt-8 flex flex-wrap items-center gap-3">
            <Link
              to={primaryTo}
              className="inline-flex h-10 items-center rounded-lg bg-white px-4 text-[14px] font-medium text-[#0a0a0a] transition-[background-color,transform] duration-150 hover:bg-[#ebebeb] active:scale-[0.98]"
            >
              {primaryLabel}
            </Link>
            {!authenticated ? (
              <a
                href={resolveApiUrl("/auth/github/login")}
                className="inline-flex h-10 items-center gap-2 rounded-lg border border-[#2e2e2e] px-4 text-[14px] font-medium text-[#f2f2f2] transition-[background-color,border-color,transform] duration-150 hover:border-[#3d3d3d] hover:bg-white/[0.04] active:scale-[0.98]"
              >
                <GitHubMark className="size-4" />
                Continue with GitHub
              </a>
            ) : null}
          </div>
        </div>

        <div className="animate-fade-up-delay-2 relative mt-16 w-full max-w-[920px]">
          <div
            aria-hidden
            className="absolute -inset-px rounded-2xl opacity-70"
            style={{
              backgroundImage: HORIZON,
              mask: "linear-gradient(#000, transparent 70%)",
              WebkitMask: "linear-gradient(#000, transparent 70%)",
            }}
          />
          <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[#0a0a0a] shadow-[0_40px_80px_-40px_rgba(0,0,0,0.9)]">
            <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
              <span className="size-2 rounded-full bg-white/15" />
              <span className="size-2 rounded-full bg-white/15" />
              <span className="size-2 rounded-full bg-white/15" />
              <span className="ml-3 font-mono text-[11px] text-[#5c5c5c]">
                PostCharges · renamed_param
              </span>
              <span className="ml-auto rounded-md bg-[#e6b84d]/15 px-2 py-0.5 text-[11px] text-[#e6b84d]">
                Needs review
              </span>
            </div>
            <div className="grid gap-0 md:grid-cols-[1.1fr_0.9fr]">
              <div className="border-b border-white/[0.06] p-5 md:border-b-0 md:border-r">
                <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#555]">
                  Call sites
                </div>
                <div className="mt-3 space-y-2">
                  {[
                    { file: "billing/charges.py:42", conf: "0.94", layer: "structural" },
                    { file: "webhooks/handler.py:118", conf: "0.71", layer: "grep" },
                    { file: "sdk/compat.py:19", conf: "0.58", layer: "agent" },
                  ].map((row, i) => (
                    <div
                      key={row.file}
                      className={[
                        "relative rounded-lg border border-white/[0.06] px-3 py-2.5",
                        i === 0 ? "bg-white/[0.03]" : "",
                      ].join(" ")}
                    >
                      {i === 0 ? (
                        <span
                          aria-hidden
                          className="absolute inset-x-3 bottom-[3px] h-[1.5px] rounded-full"
                          style={{ backgroundImage: HORIZON, boxShadow: HORIZON_GLOW }}
                        />
                      ) : null}
                      <div className="flex items-center justify-between gap-3">
                        <span className="truncate font-mono text-[12px] text-[#f2f2f2]">
                          {row.file}
                        </span>
                        <span className="font-mono text-[11px] text-[#8a8a8a]">{row.conf}</span>
                      </div>
                      <div className="mt-1 font-mono text-[10px] text-[#5c5c5c]">{row.layer}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="p-5">
                <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-[#555]">
                  Proposed patch
                </div>
                <pre className="mt-3 overflow-x-auto rounded-lg border border-white/[0.06] bg-black p-3 font-mono text-[11px] leading-relaxed">
                  <span className="text-[#f2555a]">- source=tok_visa</span>
                  {"\n"}
                  <span className="text-[#3ecf8e]">+ payment_method=tok_visa</span>
                </pre>
                <p className="mt-4 text-[12px] leading-relaxed text-[#8a8a8a]">
                  Every match shows layer + confidence. High-confidence sites ship
                  in the PR; gray-zone sites wait for your eyes.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
