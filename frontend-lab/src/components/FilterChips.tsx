import { HorizonUnderline } from "./HorizonUnderline";

export function FilterChips<T extends string>({
  options,
  value,
  onChange,
}: {
  options: Array<{ value: T | ""; label: string }>;
  value: T | "";
  onChange: (next: T | "") => void;
}) {
  return (
    <div
      className="mb-5 flex flex-wrap gap-1 border-b border-white/[0.06] pb-3"
      role="tablist"
      aria-label="Filter"
    >
      {options.map((f) => {
        const active = value === f.value;
        return (
          <button
            key={f.value || "all"}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(f.value)}
            className={[
              "relative h-8 rounded-lg px-2.5 text-[13px] tracking-[-0.01em] transition-colors duration-150 ease-out",
              active ? "text-white" : "text-[#666] hover:text-[#aaa]",
            ].join(" ")}
          >
            {f.label}
            {active ? (
              <HorizonUnderline className="absolute inset-x-2 -bottom-[13px] h-[2px] rounded-full" />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
