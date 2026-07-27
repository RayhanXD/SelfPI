export function CodeBlock({ children }: { children: string }) {
  return (
    <pre className="overflow-x-auto whitespace-pre rounded-xl border border-white/[0.07] bg-black px-3.5 py-3 font-mono text-[12px] leading-[1.65] tracking-normal text-[#a8a8a8]">
      {children}
    </pre>
  );
}
