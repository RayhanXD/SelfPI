# SelfPI Frontend

React + TypeScript + Tailwind. Design system: `frontend/design/`. Aesthetic: dusk horizon (see `TOKENS.md`).

## Routes

**Public**

- `/` — Landing
- `/login` — Sign in with GitHub
- `/auth/callback` — OAuth return (backend redirects here)

**App** (session-gated when `AUTH_REQUIRED` + OAuth configured)

- `/app` — Dashboard
- `/app/apis` — Watched APIs
- `/app/changes` — Inbox
- `/app/changes/:id` — Change detail (review cockpit)
- `/app/changes/:id/explorer` — Call-site explorer
- `/app/settings` — Account + connect repo

```bash
npm install
npm run dev
```

Opens **http://localhost:5173**. Vite proxies `/apis`, `/changes`, `/settings`, `/repos`, `/auth`, `/health` to `http://localhost:8000`.
