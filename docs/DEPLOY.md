# Deploy SelfPI

Production layout:

1. **Frontend** → Vercel (static Vite build in `frontend/`)
2. **Backend** → Docker image (repo-root `Dockerfile`) on Railway / Fly / Render / any Docker host
3. **MongoDB** → [Atlas](https://www.mongodb.com/atlas) (or any managed Mongo)

Local demo (`make` / `make reset`) is separate from this path. Use `INCLUDE_DEMO_APIS=false` in prod (default).

---

## 1. MongoDB Atlas

1. Create a free/shared cluster.
2. Add a database user and allow your host’s IPs (or `0.0.0.0/0` if the platform has dynamic egress — tighten later).
3. Copy the connection string (`mongodb+srv://…`).
4. Set on the API host:

```bash
MONGODB_URI=mongodb+srv://USER:PASS@CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=selfpi
```

Do not invent credentials in git — paste real values only in the host’s secret store.

---

## 2. Backend (Docker)

Build from the monorepo root:

```bash
docker build -t selfpi-api .
# optional local smoke with Mongo:
docker compose up --build
curl http://localhost:8000/health
```

Run on Railway / Fly / Render with this image (or connect the GitHub repo and point the Dockerfile at the repo root).

### Required env

| Variable | Example / notes |
|----------|-----------------|
| `ENV` | `production` (Secure cookies + `SameSite=None`) |
| `MONGODB_URI` | Atlas URI |
| `MONGODB_DB` | `selfpi` |
| `CORS_ORIGINS` | `https://your-app.vercel.app` (comma-separated if multiple) |
| `FRONTEND_URL` | Same origin as the Vercel app (OAuth redirects) |
| `GITHUB_OAUTH_REDIRECT_URI` | `https://api.example.com/auth/github/callback` |
| `SESSION_SECRET` | Long random string |
| `GITHUB_APP_ID` | From GitHub App |
| `GITHUB_APP_PRIVATE_KEY` | PEM contents (`\n` escaped OK) |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | App user OAuth |
| `PORT` | Set by the host (image defaults to `8000`) |

### Optional

| Variable | Notes |
|----------|--------|
| `GITHUB_APP_INSTALLATION_ID` | **Leave empty** in multi-user prod — users install from Settings |
| `GITHUB_APP_SLUG` | Optional; otherwise fetched via App JWT |
| `ANTHROPIC_API_KEY` | Adjudicator / PR copy; heuristic fallback if unset |
| `WATCH_ENABLED` / `WATCH_INTERVAL_SECONDS` | Background poller (default on / 300s) |
| `CHECKOUT_ROOT` | Default `/app/.cache/checkouts` in the image |
| `INCLUDE_DEMO_APIS` | Keep `false` |

**Clones are ephemeral:** container restarts wipe `.cache/checkouts` unless you mount a volume. That is fine — connect/detect re-clones.

Watcher starts in the FastAPI lifespan when `WATCH_ENABLED=true`.

Full variable list: `backend/.env.example`.

---

## 3. GitHub App public URLs

On the App’s settings page, set (replace with your API origin):

- **Callback URL:** `https://api.example.com/auth/github/callback`  
  (must match `GITHUB_OAUTH_REDIRECT_URI`)
- **Setup URL:** `https://api.example.com/auth/github/installed`  
  (Install App returns here with `installation_id`)
- Generate a **Client secret**; copy **Client ID**
- Make the App **public** if strangers should install it
- Permissions: Contents R/W, Pull requests R/W, Metadata R

---

## 4. Frontend (Vercel)

1. New Vercel project → import this repo.
2. **Root Directory:** `frontend`
3. Framework: Vite (auto). Build: `npm run build`. Output: `dist`.
4. Env:

```bash
VITE_API_URL=https://api.example.com
```

No trailing slash. Rebuild after changing it (`VITE_*` is compile-time).

`frontend/vercel.json` rewrites all routes to `index.html` so `/settings`, `/auth/callback`, etc. work.

Locally, leave `VITE_API_URL` empty and use `npm run dev` (Vite proxy to `:8000`).

---

## 5. Smoke checklist

1. Open the Vercel URL → **Continue with GitHub** → lands on `/auth/callback` then app.
2. **Settings** → **Install SelfPI on GitHub** → pick repos → returns to Settings with install confirmed.
3. **Connect repo** → clone + API detection runs.
4. Dashboard shows watched live APIs for that repo → **Check now** (or wait for the watcher).
5. `GET https://api.example.com/health` → `{"status":"ok"}`.

If login works but later API calls are unauthenticated: confirm `CORS_ORIGINS` includes the exact Vercel origin, `ENV=production` (or HTTPS `FRONTEND_URL`), and the browser is on HTTPS so `SameSite=None; Secure` cookies are stored.

---

## Local vs demo

| Command | Effect |
|---------|--------|
| `make` | Local API + UI + portable mongod |
| `make reset` | Clean prod-style seed (`INCLUDE_DEMO_APIS=false`) |
| `make reset-demo` / `make seed-demo` | Optional Stripe demo harness |

Do not enable the demo harness in production.
