import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { LayerBadge } from "../components/LayerBadge";
import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import { changeStatusLabel } from "../lib/status";
import type { ChangeDetail } from "../types/api";

export function ChangeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [change, setChange] = useState<ChangeDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setError(null);
    api
      .getChange(id)
      .then(setChange)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  if (error) return <p className="text-danger">{error}</p>;
  if (!change) return <p className="text-text-muted">Loading…</p>;

  const pr = change.pr;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="font-mono text-text-primary">{change.operation_id}</span>
        <span className="font-mono text-xs text-text-muted">{change.kind}</span>
        <StatusPill label={changeStatusLabel(change.status)} tone="warn" />
        <Link
          to={`/changes/${change.id}/explorer`}
          className="ml-auto text-xs text-accent hover:text-accent-hover"
        >
          Open Call-Site Explorer →
        </Link>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Spec diff */}
        <section className="rounded-lg border border-border bg-surface-1 p-4">
          <h2 className="mb-3 text-base text-text-primary">Spec diff</h2>
          {change.spec_diff ? (
            <div className="space-y-2 font-mono text-xs">
              <div className="text-text-muted">{change.spec_diff.operation_id}</div>
              {change.spec_diff.removed.map((r) => (
                <div key={r} className="rounded-sm bg-danger/15 px-2 py-1 text-danger">
                  − {r}
                </div>
              ))}
              {change.spec_diff.added.map((a) => (
                <div key={a} className="rounded-sm bg-ok/15 px-2 py-1 text-ok">
                  + {a}
                </div>
              ))}
              {change.spec_diff.raw ? (
                <pre className="mt-2 overflow-x-auto rounded-sm border border-border bg-bg p-2 text-text-secondary">
                  {change.spec_diff.raw}
                </pre>
              ) : null}
            </div>
          ) : (
            <p className="text-text-muted">No spec diff stored yet.</p>
          )}
        </section>

        {/* Call sites */}
        <section className="rounded-lg border border-border bg-surface-1 p-4">
          <h2 className="mb-3 text-base text-text-primary">
            Call sites ({change.call_sites.length})
          </h2>
          {change.call_sites.length === 0 ? (
            <p className="text-text-muted">No call sites yet.</p>
          ) : (
            <ul className="space-y-3">
              {change.call_sites.map((cs, i) => (
                <li key={`${cs.file}:${cs.span.start_line}:${i}`} className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-text-primary">
                      {cs.file}:{cs.span.start_line}
                    </span>
                    {cs.source_layer ? <LayerBadge layer={cs.source_layer} /> : null}
                  </div>
                  {cs.snippet ? (
                    <pre className="overflow-x-auto rounded-sm border border-border bg-bg px-2 py-1 font-mono text-xs text-text-secondary">
                      {cs.snippet}
                    </pre>
                  ) : null}
                  {cs.confidence != null ? <ConfidenceBar value={cs.confidence} /> : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* PR status */}
        <section className="rounded-lg border border-border bg-surface-1 p-4">
          <h2 className="mb-3 text-base text-text-primary">PR status</h2>
          {pr ? (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-text-muted">PR</dt>
                <dd className="font-mono">
                  {pr.url ? (
                    <a href={pr.url} target="_blank" rel="noreferrer">
                      #{pr.number}
                    </a>
                  ) : (
                    `#${pr.number}`
                  )}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-muted">State</dt>
                <dd className="capitalize text-text-secondary">{pr.state}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-muted">Tests</dt>
                <dd>
                  {pr.tests_passing == null ? (
                    "—"
                  ) : (
                    <StatusPill
                      label={pr.tests_passing ? "Passing" : "Failing"}
                      tone={pr.tests_passing ? "ok" : "danger"}
                    />
                  )}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-muted">Opened</dt>
                <dd className="font-mono text-xs text-text-secondary">
                  {pr.opened_at ?? "—"}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="text-text-muted">No PR opened yet.</p>
          )}
        </section>
      </div>
    </div>
  );
}
