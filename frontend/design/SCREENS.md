# Screens

IA and interaction patterns. Wire to API contract (`docs/API_CONTRACT.md`); style per [TOKENS.md](./TOKENS.md) + [COMPONENTS.md](./COMPONENTS.md).

## Shell

```
┌──────────┬─────────────────────────────────────┐
│ Sidebar  │ Top bar (title + description + acts)│
│          ├─────────────────────────────────────┤
│ nav      │ Main (scroll)                       │
│          │                                     │
└──────────┴─────────────────────────────────────┘
```

Change Detail may **omit** the generic top bar and use a sticky in-page review header instead.

Optional: faint horizon atmosphere wash at top of main column (opacity ≤ 0.07).

## Watched APIs (`/`)

**Job:** What’s watched, what’s broken, trigger check/bump.

- List shell (not a dense admin table)
- Row: name · status pill · mono meta (id · version · open count)
- Demo API: primary **Bump spec**
- Live API: secondary **Check now**
- Top bar actions: Check now + Add API

## Inbox / Change Feed (`/changes`)

**Job:** Triage detected changes.

- Filter chips (All / Detected / PR open / Merged…) with horizon underline on active
- List rows → Change Detail
- Row content: `operation_id` (mono) · status · api_id · kind · site count · PR # · date

## Change Detail (`/changes/:id`) — money screen

**Job:** Trust the fix in one pass.

Recommended layout (lab direction):

1. **Sticky header** — back to Inbox, `operation_id`, status, explanation, version range, actions (Dismiss / Rescan / Explorer / Open on GitHub)
2. **Main column** — tabs: Call sites · Spec diff · Patch
   - Call sites: selectable list + detail panel (snippet, confidence, args, path)
3. **Right rail** — PR card (number, checks, state) + short Trust blurb (layers)

Do not dump three equal opaque cards with no hierarchy. Call sites + PR are the review focus; spec diff/patch are evidence tabs.

## Call-Site Explorer (`/changes/:id/explorer`)

**Job:** Prove the scanner isn’t a black box.

- Columns: location · operation_id · args · layer · confidence
- Expand row → snippet + full CallSite JSON
- Keyboard: ↑↓ move, Enter expand
- Horizon underline on focused/expanded row

## Settings (`/settings`)

Connect a GitHub repo (installation-accessible list → select → save) plus sparse runtime status (App configured, watcher interval). No theme toggle. Don’t overbuild.

## Demo vs product

- **Bump spec** is demo-only — label clearly in UI copy near the action
- Don’t put demo controls in global nav as if they were product features
- Lab (`frontend-lab`) may hardcode mock data; production uses API

## Porting lab → production

When promoting look-and-feel from `frontend-lab` to `frontend`:

1. Copy/update tokens + `accents` helpers
2. Port shell (Sidebar, TopBar, Button, StatusPill, …)
3. Adapt pages to real `api.*` hooks (keep structure)
4. Keep this `design/` docs folder updated if anything diverged on purpose
