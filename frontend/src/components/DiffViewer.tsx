interface DiffViewerProps {
  raw?: string | null;
  removed?: string[];
  added?: string[];
  operationId?: string;
}

/** Unified-style diff — FRONTEND_GUIDELINES §3. */
export function DiffViewer({ raw, removed = [], added = [], operationId }: DiffViewerProps) {
  const lines: Array<{ kind: "meta" | "removed" | "added" | "context"; text: string }> = [];

  if (operationId) {
    lines.push({ kind: "meta", text: `operation ${operationId}` });
  }

  if (raw) {
    for (const line of raw.split("\n")) {
      if (line.startsWith("+")) lines.push({ kind: "added", text: line });
      else if (line.startsWith("-")) lines.push({ kind: "removed", text: line });
      else lines.push({ kind: "context", text: line });
    }
  } else {
    for (const r of removed) lines.push({ kind: "removed", text: `- ${r}` });
    for (const a of added) lines.push({ kind: "added", text: `+ ${a}` });
  }

  if (lines.length === 0 || (lines.length === 1 && lines[0].kind === "meta")) {
    return <p className="text-text-muted">No spec diff stored yet.</p>;
  }

  return (
    <div className="overflow-x-auto rounded-sm border border-border bg-bg font-mono text-xs">
      <table className="w-full border-collapse">
        <tbody>
          {lines.map((line, i) => (
            <tr
              key={`${i}-${line.text}`}
              className={
                line.kind === "removed"
                  ? "bg-danger/15 text-danger"
                  : line.kind === "added"
                    ? "bg-ok/15 text-ok"
                    : "text-text-secondary"
              }
            >
              <td className="select-none px-2 py-0.5 text-right text-text-muted tabular-nums w-8">
                {line.kind === "meta" ? "" : i}
              </td>
              <td className="whitespace-pre px-2 py-0.5">{line.text || " "}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
