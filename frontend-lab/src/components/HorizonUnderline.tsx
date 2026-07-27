import { HORIZON, HORIZON_GLOW } from "../lib/accents";

/** Horizontal dusk underline — active nav, tabs, selected rows, filter chips. */
export function HorizonUnderline({
  show = true,
  className = "absolute inset-x-2.5 bottom-[4px] h-[1.5px] rounded-full",
}: {
  show?: boolean;
  className?: string;
}) {
  if (!show) return null;
  return (
    <span
      aria-hidden
      className={className}
      style={{ backgroundImage: HORIZON, boxShadow: HORIZON_GLOW }}
    />
  );
}
