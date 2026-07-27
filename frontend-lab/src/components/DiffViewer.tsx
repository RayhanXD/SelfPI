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
  const lines: Array<{ kind: "meta" | "removed" | "added" | "context"; text: string }> =
    [];

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

  if (lines.length === 0) {
    return (
      <p className="text-[13px] text-[#5c5c5c]">No spec diff for this change.</p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-white/[0.07] bg-black font-mono text-[12px] leading-[1.65]">
      <table className="w-full border-collapse">
        <tbody>
          {lines.map((line, i) => (
            <tr
              key={`${i}-${line.text}`}
              className={
                line.kind === "removed"
                  ? "bg-danger/[0.08] text-[#f2555a]"
                  : line.kind === "added"
                    ? "bg-ok/[0.08] text-[#3ecf8e]"
                    : line.kind === "meta"
                      ? "text-[#5c5c5c]"
                      : "text-[#8a8a8a]"
              }
            >
              <td className="w-8 select-none px-2.5 py-[2px] text-right tabular-nums text-[#3a3a3a]">
                {line.kind === "meta" ? "" : i}
              </td>
              <td className="whitespace-pre px-2 py-[2px]">{line.text || " "}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
