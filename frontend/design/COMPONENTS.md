# Components

How to build recurring UI so the platform stays consistent. Reference implementations live in `frontend/src/components/` and pages.

## Horizon underline (active state)

Preferred active indicator — **horizontal band**, not a vertical rail.

```tsx
import { HORIZON, HORIZON_GLOW } from "../lib/accents";

<span
  aria-hidden
  className="absolute inset-x-2.5 bottom-[4px] h-[1.5px] rounded-full"
  style={{ backgroundImage: HORIZON, boxShadow: HORIZON_GLOW }}
/>
```

Parent must be `relative`. Use on: sidebar nav, tabs, selected list rows, filter chips.

Keep a shared `accents.ts` (or CSS variables mirroring [TOKENS.md](./TOKENS.md)) — do not paste hex gradients ad hoc.

## Brand mark

`BrandMark` — rounded **box** with two arrows looping out and back in, stroked in the dusk **horizon** gradient. Means self-maintaining: change leaves the system and returns as a fix.

```tsx
import { BrandMark } from "../components/BrandMark";

<BrandMark size={20} />
```

Also shipped as `public/favicon.svg`. Do not replace with a plain filled square or indigo glyph.

## Buttons

| Variant | Look |
|---------|------|
| **primary** | White bg, near-black text, `rounded-lg`, h-8, 13px medium |
| **secondary** | Transparent, `--border-strong`, white/primary text on hover fill |
| **ghost** | No border, muted text → primary on hover |
| **danger** | Danger text, quiet border, danger/10 hover |

```
height: 32px (h-8)
radius: rounded-lg (not rounded-full)
press: active:scale-[0.98]
disabled: opacity ~35%, no pointer
```

Do **not** use indigo/purple fills for primary.

## Status pill

`6px` round dot + label text. Dot color from status tokens. Label always present (a11y).

```
[●] Up to date
[●] Breaking change unhandled
```

## Layer badge

Mono chip: `grep` | `structural` | `agent`. Quiet border + faint fill. Never color-code layers with brand horizon.

## Confidence bar

Thin track (~1–3px), fill from confidence mapping, numeric `0.00`–`1.00` in mono beside it.

## List shell (preferred over heavy tables)

For Watched APIs / Inbox:

- Outer: `rounded-2xl border border-white/[0.07]`
- Rows: padding ~16–20px, hairline dividers, hover `bg-white/[0.02–0.025]`
- Title (sans, semibold) + status pill on first line
- Meta line in mono / faint

Tables are fine for Call-Site Explorer (many columns); lists are better for triage.

## Diff viewer

- Mono, black inner bg
- Removed: danger text + low-alpha danger bg
- Added: ok text + low-alpha ok bg
- Line numbers faint
- Horizontal scroll, never wrap

## Code / JSON block

Border + black/`surface-1` bg, mono 12px, `overflow-x-auto`, `whitespace-pre`.

## Sidebar

- ~248px, canvas black, right hairline
- Brand row (~60px): mark + SelfPI + repo mono
- Section eyebrows: 10px uppercase tracking-wide faint
- Nav items: `rounded-lg`, quiet hover, horizon underline when active
- Optional count chip in mono on Inbox

## Top bar

- Title ~22px semibold tight tracking
- One-line description in muted
- Actions right-aligned (secondary + primary)

## Empty / loading / error

- Empty: single muted sentence — e.g. “No changes detected yet.”
- Loading: skeleton rows (pulse surface blocks), no illustrations
- Error: danger-colored message text; keep it short

## Focus

Visible focus: outer ring using cool sky (`#7aa3c4` mix), not indigo. Never remove focus styles.
