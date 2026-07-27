# SelfPI Design System

**Canonical visual identity for the SelfPI frontend.**  
Living prototype: `frontend-lab/` (port `5180`). Production app: `frontend/src/`.

Anyone building UI (human or agent) should read this folder **before** changing styles, tokens, or shared components.

| Doc | Use when |
|-----|----------|
| [PRINCIPLES.md](./PRINCIPLES.md) | Deciding tone, craft bar, what “good” means |
| [TOKENS.md](./TOKENS.md) | Colors, horizon accent, type, spacing, radii |
| [COMPONENTS.md](./COMPONENTS.md) | Building buttons, lists, pills, horizon underlines |
| [SCREENS.md](./SCREENS.md) | Page layouts and interaction patterns |
| [DO_AND_DONT.md](./DO_AND_DONT.md) | Guardrails and anti-patterns |

## Product context

SelfPI is a **startup-grade developer product**: watch API specs, find breaking-change call sites, open fix PRs. The UI’s job is **trust** — make the pipeline’s reasoning visible — with calm, expensive craft (Linear-inspired, not a Linear clone).

## Source of truth order

1. This folder (`frontend/design/`) — visual identity & how to build
2. `docs/FRONTEND_GUIDELINES.md` — screen inventory + product UX rules (defers here for tokens)
3. `frontend-lab/` — reference implementation of the look
4. `frontend/src/` — production wiring to the API

When tokens or horizon values change, update **TOKENS.md** and the lab (`frontend-lab/src/lib/accents.ts` + `index.css`) in the same change, then port to `frontend/src`.
