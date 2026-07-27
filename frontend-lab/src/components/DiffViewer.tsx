export function DiffViewer({
  raw,
  removed = [],
  added = [],
  operationId,
}: {
  raw?: string | null;
  removed?: string[];
  added?: string[];
  operationId?: string;
}) {
  const lines: Array<{ kind: "meta" | "removed" | "added" | "context"; text: string }> = [];

  if (operationId) lines.push({ kind: "meta", text: `operation ${operationId}` });

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

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-black font-mono text-[12px] leading-[1.6]">
      <table className="w-full border-collapse">
        <tbody>
          {lines.map((line, i) => (
            <tr
              key={`${i}-${line.text}`}
              className={
                line.kind === "removed"
                  ? "bg-danger/[0.07] text-[#ff6b6b]"
                  : line.kind === "added"
                    ? "bg-ok/[0.07] text-[#3dd68c]"
                    : line.kind === "meta"
                      ? "text-text-faint"
                      : "text-text-muted"
              }
            >
              <td className="w-7 select-none px-2 py-[1px] text-right tabular-nums text-text-faint/70">
                {line.kind === "meta" ? "" : i}
              </td>
              <td className="whitespace-pre px-2 py-[1px]">{line.text || " "}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
