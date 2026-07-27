# Screens

IA and interaction patterns. Wire to API contract (`docs/API_CONTRACT.md`); style per [TOKENS.md](./TOKENS.md) + [COMPONENTS.md](./COMPONENTS.md).

## Public surface

| Path | Job |
|------|-----|
| `/` | Marketing landing — brand, one promise, CTA into product |
| `/login` | Sign in with GitHub (or continue without when OAuth unset) |
| `/auth/callback` | OAuth return — reload session, route to `/app` or `/login?error=` |

## Product shell (`/app/*`)

Gated by `RequireAuth` when `login_required && !authenticated`.

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

## Dashboard (`/app`)

**Job:** Health overview — what needs review, setup checklist, recent activity.

## Watched APIs (`/app/apis`)

**Job:** What’s watched, what’s broken, trigger check/bump.

- List shell (not a dense admin table)
- Row: name · status pill · mono meta (id · version · open count)
- Demo API: primary **Bump spec**
- Live API: secondary **Check now**

## Inbox / Change Feed (`/app/changes`)

**Job:** Triage detected changes.

- Filter chips (All / Detected / PR open / Merged…) with horizon underline on active
- List rows → Change Detail
- Row content: `operation_id` (mono) · status · api_id · kind · site count · PR # · date

## Change Detail (`/app/changes/:id`) — money screen

**Job:** Trust the fix in one pass.

1. **Sticky header** — back to Inbox, `operation_id`, status, explanation, version range, actions
2. **Main column** — tabs: Call sites · Spec diff · Patch
3. **Right rail** — PR card + Trust blurb (layers)

## Call-Site Explorer (`/app/changes/:id/explorer`)

**Job:** Prove the scanner isn’t a black box.

- Columns: location · operation_id · args · layer · confidence
- Expand row → snippet + full CallSite JSON
- Keyboard: ↑↓ move, Enter expand

## Settings (`/app/settings`)

Connect a GitHub repo + account (Login with GitHub / sign out). Sparse runtime status. No theme toggle.

## Demo vs product

- **Bump spec** is demo-only — label clearly near the action
- Don’t put demo controls in global nav
- Lab (`frontend-lab`) may hardcode mock data; production uses API + OAuth

## Porting lab → production

1. Copy/update tokens + `accents` helpers
2. Port shell (Sidebar, TopBar, Button, StatusPill, …)
3. Adapt pages to real `api.*` hooks (keep structure)
4. Keep this `design/` docs folder updated if anything diverged on purpose
