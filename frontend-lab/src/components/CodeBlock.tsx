export function CodeBlock({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto whitespace-pre rounded-lg border border-border bg-black px-3 py-2.5 font-mono text-[12px] leading-[1.6] text-text-secondary">
      {children}
    </pre>
  );
}
