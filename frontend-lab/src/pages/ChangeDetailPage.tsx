import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/Button";
import { CodeBlock } from "../components/CodeBlock";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { DiffViewer } from "../components/DiffViewer";
import { Flash } from "../components/EmptyState";
import { HorizonUnderline } from "../components/HorizonUnderline";
import { LayerBadge } from "../components/LayerBadge";
import { StatusPill } from "../components/StatusPill";
import { MOCK_CHANGE_DETAIL } from "../data/mock";
import { changeStatusLabel, changeStatusTone } from "../lib/status";

type Tab = "sites" | "diff" | "fix";

export function ChangeDetailPage() {
  const change = MOCK_CHANGE_DETAIL;
  const pr = change.pr;
  const [tab, setTab] = useState<Tab>("sites");
  const [selected, setSelected] = useState(0);
  const [flash, setFlash] = useState<string | null>(null);
  const site = change.call_sites[selected];

  return (
    <div className="flex min-h-full flex-col">
      <div className="sticky top-0 z-10 border-b border-white/[0.06] bg-[#050505]/90 px-6 py-4 backdrop-blur-xl md:px-8">
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 space-y-2">
            <Link
              to="/changes"
              className="inline-flex text-[12px] text-[#666] transition-colors duration-150 hover:text-[#aaa]"
            >
              ← Inbox
            </Link>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="font-mono text-[22px] font-medium tracking-tight text-white">
                {change.operation_id}
              </h2>
              <StatusPill
                label={changeStatusLabel(change.status)}
                tone={changeStatusTone(change.status)}
              />
            </div>
            {change.explanation ? (
              <p className="max-w-2xl text-[13px] leading-relaxed text-[#a8a8a8]">
                {change.explanation}
              </p>
            ) : null}
            <div className="flex flex-wrap items-center gap-x-2.5 text-[12px] text-[#666]">
              <span className="font-mono tracking-normal">{change.kind}</span>
              <span className="text-[#3a3a3a]">·</span>
              <span className="font-mono tracking-normal">
                {change.from_version} → {change.to_version}
              </span>
              <span className="text-[#3a3a3a]">·</span>
              <span className="font-mono tracking-normal">{change.repo}</span>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Button
              variant="ghost"
              onClick={() => setFlash("Dismissed (lab mock).")}
            >
              Dismiss
            </Button>
            <Button
              variant="secondary"
              onClick={() => setFlash("Rescan queued (lab mock).")}
            >
              Rescan
            </Button>
            <Link
              to={`/changes/${change.id}/explorer`}
              className="inline-flex h-8 items-center rounded-lg border border-[#2e2e2e] px-3 text-[13px] font-medium tracking-[-0.01em] text-[#f2f2f2] transition-[background-color,border-color,transform] duration-150 hover:border-[#3d3d3d] hover:bg-white/[0.04] active:scale-[0.98]"
            >
              Explorer
            </Link>
            <Button
              variant="primary"
              onClick={() => {
                if (pr?.url) window.open(pr.url, "_blank", "noopener,noreferrer");
              }}
            >
              Open on GitHub
            </Button>
          </div>
        </div>
        {flash ? (
          <div className="mx-auto mt-3 max-w-[1280px]">
            <Flash tone="info">{flash}</Flash>
          </div>
        ) : null}
      </div>

      <div className="mx-auto grid w-full max-w-[1280px] flex-1 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="border-b border-white/[0.06] px-6 py-5 md:px-8 lg:border-b-0 lg:border-r">
          <div className="mb-5 flex gap-1 border-b border-white/[0.06]" role="tablist">
            {(
              [
                ["sites", `Call sites · ${change.call_sites.length}`],
                ["diff", "Spec diff"],
                ["fix", "Patch"],
              ] as const
            ).map(([id, label]) => {
              const active = tab === id;
              return (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => setTab(id)}
                  className={[
                    "relative h-9 px-3 text-[13px] tracking-[-0.01em] transition-colors duration-150",
                    active ? "text-white" : "text-[#666] hover:text-[#aaa]",
                  ].join(" ")}
                >
                  {label}
                  <HorizonUnderline
                    show={active}
                    className="absolute inset-x-3 -bottom-px h-[2px] rounded-full"
                  />
                </button>
              );
            })}
          </div>

          {tab === "sites" ? (
            <div className="grid gap-5 lg:grid-cols-[240px_minmax(0,1fr)]">
              <ul className="space-y-0.5">
                {change.call_sites.map((cs, i) => {
                  const active = selected === i;
                  return (
                    <li key={`${cs.file}:${cs.span.start_line}`}>
                      <button
                        type="button"
                        onClick={() => setSelected(i)}
                        className={[
                          "relative w-full rounded-lg px-2.5 py-2.5 text-left transition-colors duration-150",
                          active
                            ? "bg-white/[0.06] text-white"
                            : "text-[#888] hover:bg-white/[0.03] hover:text-[#ccc]",
                        ].join(" ")}
                      >
                        <HorizonUnderline show={active} />
                        <div className="truncate font-mono text-[12px] tracking-normal">
                          {cs.file}:{cs.span.start_line}
                        </div>
                        <div className="mt-1 flex items-center gap-2 pb-1">
                          {cs.source_layer ? (
                            <LayerBadge layer={cs.source_layer} />
                          ) : null}
                          {cs.confidence != null ? (
                            <span className="font-mono text-[11px] tracking-normal text-[#666]">
                              {cs.confidence.toFixed(2)}
                            </span>
                          ) : null}
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>

              {site ? (
                <div className="space-y-3 rounded-2xl border border-white/[0.07] bg-[#0a0a0a] p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="font-mono text-[13px] tracking-normal text-white">
                      {site.file}
                      <span className="text-[#666]">:{site.span.start_line}</span>
                    </div>
                    {site.source_layer ? (
                      <LayerBadge layer={site.source_layer} />
                    ) : null}
                  </div>
                  {site.snippet ? (
                    <pre className="overflow-x-auto whitespace-pre rounded-xl bg-black px-3 py-2.5 font-mono text-[12px] leading-relaxed tracking-normal text-[#a8a8a8]">
                      {site.snippet}
                    </pre>
                  ) : null}
                  <div className="flex flex-wrap items-center gap-5 border-t border-white/[0.06] pt-3">
                    <Meta label="Confidence">
                      {site.confidence != null ? (
                        <ConfidenceBar value={site.confidence} />
                      ) : (
                        "—"
                      )}
                    </Meta>
                    <Meta label="Args">
                      <span className="font-mono text-[12px] tracking-normal text-[#a8a8a8]">
                        {site.args.map((a) => a.name).filter(Boolean).join(", ") ||
                          "—"}
                      </span>
                    </Meta>
                    <Meta label="Path">
                      <span className="font-mono text-[12px] tracking-normal text-[#a8a8a8]">
                        {[site.receiver, ...site.path].filter(Boolean).join(".")}
                        {site.invoked ? "()" : ""}
                      </span>
                    </Meta>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}

          {tab === "diff" ? (
            <DiffViewer
              operationId={change.spec_diff?.operation_id}
              raw={change.spec_diff?.raw}
              removed={change.spec_diff?.removed}
              added={change.spec_diff?.added}
            />
          ) : null}

          {tab === "fix" ? (
            change.patch_preview ? (
              <CodeBlock>{change.patch_preview}</CodeBlock>
            ) : (
              <p className="text-[13px] text-[#5c5c5c]">No patch preview yet.</p>
            )
          ) : null}
        </div>

        <aside className="px-6 py-5">
          <div className="sticky top-[108px] space-y-5">
            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#555]">
                Pull request
              </div>
              {pr ? (
                <div className="space-y-3 rounded-2xl border border-white/[0.07] bg-[#0a0a0a] p-4">
                  <div className="flex items-center justify-between gap-2">
                    <a
                      href={pr.url ?? "#"}
                      className="font-mono text-[14px] tracking-normal text-white transition-opacity hover:opacity-80"
                    >
                      #{pr.number}
                    </a>
                    <StatusPill
                      label={pr.tests_passing ? "Checks passing" : "Checks failing"}
                      tone={pr.tests_passing ? "ok" : "danger"}
                    />
                  </div>
                  <Row label="State">
                    <span className="capitalize">{pr.state}</span>
                  </Row>
                  <Row label="Opened">
                    <span className="font-mono text-[12px] tracking-normal">
                      {pr.opened_at?.replace("T", " ").replace("Z", "")}
                    </span>
                  </Row>
                  <div className="pt-1">
                    <Button
                      variant="primary"
                      className="w-full"
                      onClick={() => {
                        if (pr.url) window.open(pr.url, "_blank", "noopener,noreferrer");
                      }}
                    >
                      Open on GitHub
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-[13px] text-[#8a8a8a]">No PR opened yet.</p>
              )}
            </div>

            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.1em] text-[#555]">
                Trust
              </div>
              <div className="space-y-2 rounded-2xl border border-white/[0.07] bg-[#0a0a0a] p-4 text-[12px] leading-relaxed text-[#a8a8a8]">
                <p>
                  High-confidence sites are auto-included. Gray-zone sites were
                  adjudicated — open Explorer for full IR.
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  {(["structural", "grep", "agent"] as const).map((layer) => (
                    <LayerBadge key={layer} layer={layer} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

function Meta({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1">
      <div className="text-[11px] text-[#666]">{label}</div>
      {children}
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 text-[13px]">
      <span className="text-[#666]">{label}</span>
      <span className="text-[#a8a8a8]">{children}</span>
    </div>
  );
}
