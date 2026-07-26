interface CodeBlockProps {
  children: string;
  className?: string;
}

export function CodeBlock({ children, className = "" }: CodeBlockProps) {
  return (
    <pre
      className={[
        "overflow-x-auto rounded-sm border border-border bg-surface-1 p-3 font-mono text-xs text-text-secondary whitespace-pre",
        className,
      ].join(" ")}
    >
      {children}
    </pre>
  );
}
