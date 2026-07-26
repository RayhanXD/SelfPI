import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button } from "../components/Button";
import { CodeBlock } from "../components/CodeBlock";
import { ConfidenceBar } from "../components/ConfidenceBar";
import { DiffViewer } from "../components/DiffViewer";
import { EmptyState, ErrorState, SkeletonRows } from "../components/EmptyState";
import { LayerBadge } from "../components/LayerBadge";
import { StatusPill } from "../components/StatusPill";
import { api } from "../lib/api";
import { changeStatusLabel, changeStatusTone } from "../lib/status";
import { useAsync } from "../lib/useAsync";

export function ChangeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: change, error, loading, reload } = useAsync(
    () => api.getChange(id!),
    [id],
  );
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const onDismiss = async () => {
    if (!change) return;
    setBusy("dismiss");
    setActionError(null);
    try {
      await api.dismissChange(change.id);
      reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Dismiss failed");
    } finally {
      setBusy(null);
    }
  };

  const onRescan = async () => {
    if (!change) return;
    setBusy("rescan");
    setActionError(null);
    try {
      await api.rescanChange(change.id);
      reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Rescan failed");
    } finally {
      setBusy(null);
    }
  };

  const onOpenPr = async () => {
    if (!change) return;
    setBusy("open-pr");
    setActionError(null);
    try {
      await api.openPr(change.id);
      reload();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Open PR failed");
    } finally {
      setBusy(null);
    }
  };

  if (error || actionError) return <ErrorState message={error ?? actionError!} />;
  if (loading || !change) return <SkeletonRows cols={3} />;

  const pr = change.pr;
  const canOpenPr =
    change.status === "detected" &&
    change.call_sites.length > 0 &&
    !(pr?.url);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="text-xs text-text-muted hover:text-accent"
        >
          ← Back
        </button>
        <span className="font-mono text-text-primary">{change.operation_id}</span>
        <span className="font-mono text-xs text-text-muted">{change.kind}</span>
        <StatusPill
          label={changeStatusLabel(change.status)}
          tone={changeStatusTone(change.status)}
        />
        <span className="font-mono text-xs text-text-muted">
          {change.from_version} → {change.to_version}
        </span>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          {canOpenPr ? (
            <Button variant="primary" onClick={onOpenPr} disabled={busy === "open-pr"}>
              {busy === "open-pr" ? "Opening…" : "Open PR"}
            </Button>
          ) : null}
          <Button onClick={onRescan} disabled={busy === "rescan"}>
            {busy === "rescan" ? "Scanning…" : "Rescan"}
          </Button>
          <Button variant="danger" onClick={onDismiss} disabled={busy === "dismiss"}>
            {busy === "dismiss" ? "…" : "Dismiss"}
          </Button>
          <Link
            to={`/changes/${change.id}/explorer`}
            className="rounded-md border border-border-strong px-2.5 py-1 text-[13px] text-text-secondary hover:bg-surface-3 hover:text-text-primary"
          >
            Call-Site Explorer →
          </Link>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-lg border border-border bg-surface-1 p-4">
          <h2 className="mb-3 text-base text-text-primary">Spec diff</h2>
          <DiffViewer
            operationId={change.spec_diff?.operation_id ?? change.operation_id}
            raw={change.spec_diff?.raw}
            removed={change.spec_diff?.removed}
            added={change.spec_diff?.added}
          />
          {change.detail && Object.keys(change.detail).length > 0 ? (
            <div className="mt-3">
              <div className="mb-1 text-xs uppercase tracking-wide text-text-muted">Detail</div>
              <CodeBlock>{JSON.stringify(change.detail, null, 2)}</CodeBlock>
            </div>
          ) : null}
        </section>

        <section className="rounded-lg border border-border bg-surface-1 p-4">
          <h2 className="mb-3 text-base text-text-primary">
            Call sites ({change.call_sites.length})
          </h2>
          {change.call_sites.length === 0 ? (
            <EmptyState message="No call sites yet." />
          ) : (
            <ul className="space-y-3">
              {change.call_sites.map((cs, i) => (
                <li
                  key={`${cs.file}:${cs.span.start_line}:${i}`}
                  className="space-y-1 border-b border-border pb-3 last:border-0 last:pb-0"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs text-text-primary">
                      {cs.file}:{cs.span.start_line}
                    </span>
                    {cs.source_layer ? <LayerBadge layer={cs.source_layer} /> : null}
                  </div>
                  {cs.snippet ? (
                    <pre className="overflow-x-auto rounded-sm border border-border bg-bg px-2 py-1 font-mono text-xs text-text-secondary whitespace-pre">
                      {cs.snippet}
                    </pre>
                  ) : null}
                  {cs.confidence != null ? <ConfidenceBar value={cs.confidence} /> : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="rounded-lg border border-border bg-surface-1 p-4">
          <h2 className="mb-3 text-base text-text-primary">PR status</h2>
          {pr?.url ? (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-text-muted">PR</dt>
                <dd className="font-mono">
                  <a href={pr.url} target="_blank" rel="noreferrer" className="text-accent">
                    #{pr.number}
                  </a>
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
                    <span className="text-text-muted">—</span>
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
              {change.repo ? (
                <div className="flex justify-between gap-4">
                  <dt className="text-text-muted">Repo</dt>
                  <dd className="font-mono text-xs text-text-secondary">{change.repo}</dd>
                </div>
              ) : null}
            </dl>
          ) : (
            <EmptyState
              message={
                canOpenPr
                  ? "No PR yet. Configure the GitHub App, then click Open PR."
                  : "No PR opened yet."
              }
            />
          )}
        </section>
      </div>
    </div>
  );
}
