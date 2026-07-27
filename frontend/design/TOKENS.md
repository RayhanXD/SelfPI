# Tokens

Canonical values. Implement as CSS variables (Tailwind `@theme` or equivalent). Keep `frontend/src/index.css` and `frontend/src/lib/accents.ts` in sync when these change.

## Surfaces (black / white quiet)

| Token | Hex | Role |
|-------|-----|------|
| `--bg` / `--surface-0` | `#050505` | App canvas |
| `--surface-1` | `#0c0c0c` | Panels, list chrome |
| `--surface-2` | `#121212` | Raised / hover base |
| `--surface-3` | `#1a1a1a` | Active row / strong hover |
| `--surface-hover` | `#1c1c1c` | Interactive hover fill |

Prefer `border-white/[0.06]`–`/[0.08]` over hard gray borders when composing new UI — reads softer on pure black.

## Text

| Token | Hex | Role |
|-------|-----|------|
| `--text-primary` | `#f2f2f2` | Titles, primary labels |
| `--text-secondary` | `#a8a8a8` | Supporting copy |
| `--text-muted` | `#8a8a8a` | Secondary UI |
| `--text-faint` | `#5c5c5c` | Meta, section eyebrows |

## Borders

| Token | Hex | Role |
|-------|-----|------|
| `--border` | `#1a1a1a` | Default hairline |
| `--border-subtle` | `#141414` | Quieter splits |
| `--border-strong` | `#2e2e2e` | Buttons, stronger edges |

## Status (semantic only — not brand)

| Token | Hex | Use |
|-------|-----|-----|
| `--ok` | `#3ecf8e` | Up to date, checks passing, high confidence |
| `--warn` | `#e6b84d` | Needs review, medium confidence |
| `--danger` | `#f2555a` | Unhandled break, failing checks, low confidence |
| `--info` | `#6b9fd4` | Neutral info (e.g. PR open) |

### Confidence mapping

```
>= 0.85  → --ok
0.6–0.85 → --warn
< 0.6    → --danger
```

Always show the numeric value in mono next to any confidence bar. Never color alone.

## Horizon accent (the “rainbow”)

**Not** a candy rainbow. **Dusk horizon** — muted horizontal band. Brand only.

```ts
// frontend/src/lib/accents.ts (canonical JS strings)

export const HORIZON =
  "linear-gradient(90deg, #e8a07a 0%, #efc28a 20%, #d989a5 45%, #9a8fc0 70%, #7aa3c4 100%)";
// sand → gold → rose → lilac → cool sky

export const HORIZON_SOFT =
  "linear-gradient(90deg, #f0b090 0%, #f5d09a 22%, #e39ab3 48%, #a99ad0 74%, #8bb4d0 100%)";
// slightly brighter — brand chip only

export const HORIZON_GLOW =
  "0 0 12px rgba(232,160,122,0.35), 0 0 20px rgba(122,163,196,0.2)";
```

### Where horizon is allowed

- Brand mark (`BrandMark` — box + looping arrows)
- Active nav / tab / row **underline** (horizontal, ~1.5–2px)
- Optional faint atmospheric wash at top of main pane (opacity ≤ ~0.07)

### Where horizon is forbidden

- Button fills (primary is **white** on black)
- Full-bleed backgrounds
- Text fills / gradient text on body copy
- Status indicators (use semantic status tokens)
- Vertical candy rails (old pattern — do not revive)

There is **no** solid `--accent` indigo. Primary actions use white fill / black text. Focus rings may use a cool sky tint derived from the horizon’s last stop (`#7aa3c4`).

## Typography

| Role | Family |
|------|--------|
| UI | `"Plus Jakarta Sans", ui-sans-serif, system-ui, sans-serif` |
| Code / paths / IDs / JSON | `"IBM Plex Mono", ui-monospace, monospace` |

Load via Google Fonts (or self-host later):

```
Plus Jakarta Sans: 400, 500, 600
IBM Plex Mono: 400, 500
```

### Scale (guide)

| Use | Size | Weight | Tracking |
|-----|------|--------|----------|
| Page title | ~22px | 600 | -0.04em |
| Section / row title | 14–15px | 600 | -0.03em |
| Body / controls | 13–13.5px | 400–500 | -0.01em – -0.015em |
| Meta / mono | 10–12px | 400–500 | 0 (mono) |
| Eyebrow labels | 10px | 600 | +0.12em uppercase |

Body letter-spacing ≈ `-0.015em`. Mono never tightens.

## Spacing & radius

- **Grid:** 4px base (4, 8, 12, 16, 24, 32)
- **Radius:** `rounded-md` / `rounded-lg` (~6–8px) for controls; `rounded-2xl` for large list shells
- **Not** full pills for primary buttons (that’s Vercel-default; we use soft rectangles)
- Sidebar ~248px; content max ~1040–1080px for list pages; Change Detail can go wider (~1280)

## Motion

- Duration ~150ms
- Easing: `ease-out` or `cubic-bezier(0.16, 1, 0.3, 1)` for emphasis
- Prefer `transition-[background-color,border-color,transform,color]` — never `transition: all`
- Buttons: `active:scale-[0.98]`
