# SelfPI Frontend

React + TypeScript + Tailwind dashboard (dark-minimal). Screens:

- Watched APIs (`/`)
- Change Feed (`/changes`)
- Change Detail (`/changes/:id`) — spec diff · call sites · PR status
- Call-Site Explorer (`/changes/:id/explorer`)
- Settings (`/settings`)

Tokens and component rules: `../docs/FRONTEND_GUIDELINES.md`.

```bash
npm install
npm run dev
```

Vite proxies `/apis`, `/changes`, and `/health` to `http://localhost:8000`.
