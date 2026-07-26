# Frontend Guidelines — Self-Maintaining APIs

Aesthetic: **dark, minimal developer tool** (Linear / Vercel / GitHub-dark lineage). Dense, calm, information-first. The UI's job is to make the pipeline's reasoning *visible* and trustworthy — not to decorate.

---

## 1. Principles

1. **Information density over whitespace.** This is a tool for engineers scanning state quickly. Prefer compact tables and tight vertical rhythm to airy marketing layouts.
2. **One accent, used sparingly.** Color carries meaning (status, confidence), not decoration. If everything is highlighted, nothing is.
3. **Monospace for anything code-shaped.** File paths, symbols, diffs, JSON, operation IDs.
4. **Show the reasoning.** Every flagged call site displays its source layer and confidence. No black boxes.
5. **Flat, not glossy.** No gradients, shadows-as-decoration, or skeuomorphism. Borders and subtle surface steps define structure.
6. **Keyboard-friendly.** Primary lists navigable by keyboard; visible focus states.

## 2. Design tokens

### Color (dark theme is the default and only v1 theme)

```
/* surfaces */
--bg:            #0D0D0F;   /* app background */
--surface-1:     #141417;   /* cards, panels */
--surface-2:     #1B1B1F;   /* raised: table header, hover */
--surface-3:     #232329;   /* input, active row */

/* text */
--text-primary:  #ECECEE;
--text-secondary:#A1A1A8;
--text-muted:    #6E6E76;

/* borders */
--border:        #26262C;
--border-strong: #35353D;

/* accent (single) */
--accent:        #6E5AE6;   /* indigo — primary actions, links, focus */
--accent-hover:  #7E6DF0;

/* status semantics */
--ok:            #3FB950;   /* up to date / tests passing / merged */
--warn:          #D9A429;   /* change detected / needs review */
--danger:        #E5534B;   /* breaking change unhandled / tests failing */
--info:          #4C8FE0;   /* neutral informational */
```

### Confidence scale (Call-Site Explorer)

Map a call site's `confidence` (0–1) to color, so trust is visible at a glance:

```
>= 0.85  --ok      (high — auto-included)
0.6–0.85 --warn    (medium — worth a glance)
< 0.6    --danger  (low — agent-adjudicated / needs human eyes)
```

### Typography

```
--font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;   /* UI text */
--font-mono: "JetBrains Mono", ui-monospace, "SF Mono", monospace; /* code, paths, JSON */

--text-xs:  12px;   /* metadata, table secondary */
--text-sm:  13px;   /* default body / table cells */
--text-base:14px;   /* section labels */
--text-lg:  16px;   /* panel titles */
--text-xl:  20px;   /* page titles */
line-height: 1.5 body, 1.25 headings.
```

### Spacing & shape

```
--space: 4px base grid (use multiples: 4, 8, 12, 16, 24, 32).
--radius-sm: 4px;  (inputs, chips)
--radius:    6px;  (cards, buttons)
--radius-lg: 10px; (panels/modals)
border width: 1px, --border by default.
```

## 3. Components

**Status dot / pill** — small colored dot + label using the status semantics. Used in Watched APIs and the Change Feed. Never rely on color alone; always pair with a label for accessibility.

**Data table** — the workhorse. `--surface-2` sticky header, `--text-muted` uppercase 12px column labels, 1px `--border` row separators, `--surface-2` row hover, `--surface-3` selected row. Monospace for path/symbol columns.

**Diff viewer** — unified or split; removed lines tinted `--danger` (low-alpha bg), added lines `--ok` (low-alpha bg), monospace, line numbers in `--text-muted`.

**Confidence bar** — a thin horizontal bar filled per the confidence scale, with the numeric value in mono beside it.

**Layer badge** — small mono chip showing provenance: `grep`, `structural`, `agent`. Lets a reviewer see how a call site was found.

**Buttons** — primary = `--accent` bg / white text; secondary = transparent with `--border-strong`; destructive = `--danger`. 6px radius, 13px, subtle hover lightening only.

**Code / JSON block** — `--surface-1` bg, `--border`, mono, 12–13px, horizontal scroll not wrap.

**Empty & loading states** — muted, single-line, no illustrations. e.g. "No changes detected yet." Skeleton rows for tables.

## 4. Layout

- **Left sidebar** (fixed, ~220px, `--surface-1`): app name, nav (Watched APIs, Changes, Settings), connected-repo indicator at the bottom.
- **Top bar** (thin): current page title, global actions (e.g. "Add API"), and the manual "Check now" trigger.
- **Main content**: single scroll column; detail views use a two- or three-panel split.
- Max content width for reading views ~1200px; tables may go full width.

## 5. Screen specs (map to design doc §12)

**Watched APIs (home)** — table: API name, current version, status pill, last checked, # open changes. Row click → that API's change feed.

**Change Feed** — reverse-chronological list/table of detected changes: API, operation ID (mono), change kind, # affected call sites, PR status, detected-at. Filter by status (esp. "unhandled").

**Change Detail (the money screen)** — three panels:
- *Left:* spec diff (old vs new) for the affected operation.
- *Center:* affected call sites — file path (mono), line, snippet, layer badge, confidence bar.
- *Right:* generated PR preview — title, explanation, the patch, and PR/test status.

**Call-Site Explorer** — the distinctive screen. A table of the IR records for a change with columns: file:line (mono), `operation_id`, matched args, `source_layer` badge, confidence bar. Expandable row reveals the full Call-Site IR JSON. This is where the tool proves it isn't a black box.

**PR Status** — compact view or column: PR number/link, state (open/merged/closed), tests passing/failing, opened-at.

## 6. Accessibility

- Never encode meaning in color alone — always pair with text/icon (status pills, confidence values).
- Visible focus ring (`--accent`, 2px) on all interactive elements.
- Target WCAG AA contrast; the token text colors are chosen against their surfaces to meet it.

## 7. Don'ts

- No gradients, drop shadows for decoration, or animated flourishes.
- No second accent color. Status colors are semantic, not brand accents.
- No wrapping of code/paths — scroll instead.
- No dense paragraphs of prose in the UI; labels and values, not sentences.
