import { useId } from "react";
import { HORIZON_GLOW } from "../lib/accents";

/**
 * SelfPI app mark — box with arrows looping out and back in,
 * stroked in the dusk horizon gradient.
 */
export function BrandMark({
  size = 20,
  className = "",
  glow = true,
}: {
  size?: number;
  className?: string;
  glow?: boolean;
}) {
  const uid = useId().replace(/:/g, "");
  const gradId = `horizon-${uid}`;

  return (
    <span
      className={["inline-flex shrink-0 items-center justify-center", className].join(
        " ",
      )}
      style={
        glow
          ? { filter: `drop-shadow(${HORIZON_GLOW.split(",")[0]})` }
          : undefined
      }
      aria-hidden
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient
            id={gradId}
            x1="2"
            y1="16"
            x2="30"
            y2="16"
            gradientUnits="userSpaceOnUse"
          >
            <stop offset="0%" stopColor="#e8a07a" />
            <stop offset="22%" stopColor="#efc28a" />
            <stop offset="48%" stopColor="#d989a5" />
            <stop offset="74%" stopColor="#9a8fc0" />
            <stop offset="100%" stopColor="#7aa3c4" />
          </linearGradient>
        </defs>
        <rect
          x="10"
          y="10"
          width="12"
          height="12"
          rx="3"
          stroke={`url(#${gradId})`}
          strokeWidth="1.8"
        />
        <path
          d="M20.5 10.8 C24.8 8.6 27.2 11.8 25.4 15.6 C24.2 18.2 20.8 19.2 18.2 17.6"
          stroke={`url(#${gradId})`}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M19.55 16.05 L17.35 17.95 L19.85 19.15"
          stroke={`url(#${gradId})`}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M11.5 21.2 C7.2 23.4 4.8 20.2 6.6 16.4 C7.8 13.8 11.2 12.8 13.8 14.4"
          stroke={`url(#${gradId})`}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M12.45 15.95 L14.65 14.05 L12.15 12.85"
          stroke={`url(#${gradId})`}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}
