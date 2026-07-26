# SelfPI Frontend

React + TypeScript + Tailwind dashboard (dark-minimal). Screens per `docs/FRONTEND_GUIDELINES.md`:

- Watched APIs (`/`) — status table, Check now, demo **Bump spec**
- Change Feed (`/changes`) — filter by status / api_id
- Change Detail (`/changes/:id`) — spec diff · call sites · PR status
- Call-Site Explorer (`/changes/:id/explorer`) — IR table, expand JSON, ↑↓/Enter
- Settings (`/settings`)

```bash
npm install
npm run dev
```

Vite proxies `/apis`, `/changes`, and `/health` to `http://localhost:8000`.
