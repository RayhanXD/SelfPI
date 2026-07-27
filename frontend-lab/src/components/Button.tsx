import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

const variants: Record<Variant, string> = {
  primary:
    "bg-white text-[#0a0a0a] border-transparent hover:bg-[#ebebeb] active:scale-[0.98]",
  secondary:
    "bg-transparent text-[#f2f2f2] border-[#2e2e2e] hover:bg-white/[0.04] hover:border-[#3d3d3d] active:scale-[0.98]",
  ghost:
    "bg-transparent text-[#8a8a8a] border-transparent hover:bg-white/[0.04] hover:text-[#f2f2f2] active:scale-[0.98]",
  danger:
    "bg-transparent text-[#f2555a] border-[#2e2e2e] hover:bg-[#f2555a]/10 hover:border-[#f2555a]/35 active:scale-[0.98]",
};

export function Button({
  variant = "secondary",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      className={[
        "inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border px-3 text-[13px] font-medium tracking-[-0.01em] transition-[background-color,border-color,transform,color] duration-150 ease-out disabled:pointer-events-none disabled:opacity-35",
        variants[variant],
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
