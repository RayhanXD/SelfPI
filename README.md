# SelfPI — Self-Maintaining APIs

Watch an upstream API spec, detect breaking changes, find affected call sites in a repo, and open a PR that fixes them. **"Dependabot for APIs."**

See `docs/` for the full design, PRD, engineering plan, API contract, and frontend guidelines. Follow `CLAUDE.md` for repo conventions.

## Repo layout

```
backend/     Python — watcher, diff, scanner, patcher, REST API, MongoDB
frontend/    React + TypeScript + Tailwind (dark-minimal dashboard)
fixtures/    Diff triples, golden IR records, sample Python repo
docs/        Design + product docs
```

## Prerequisites

- Python 3.11+
- Node 20+
- MongoDB — `make` starts a **local portable mongod** automatically (no Docker).

## Run everything

```bash
make
```

- UI:  http://localhost:5173 — **Bump spec** on `Stripe (demo)`
- API: http://localhost:8000/health
- Reset polluted DB: `make reset`

`make stop` kills API, UI, and local mongod.

## Demo vs live

| API id | Mode | Action |
|--------|------|--------|
| `stripe-demo` | demo | **Bump spec** — pushes `source → payment_method` and runs the pipeline |
| `stripe` | live | **Check now** — polls the real Stripe OpenAPI |

Do not bump the live API or check the demo API — they are split so they cannot poison each other.

## Demo consumer (local test target)

SelfPI scans a tiny Stripe app in `demo-consumer/` (gitignored — not part of this repo).

```bash
python3 scripts/bootstrap_demo_consumer.py   # creates folder + local git repo
```

Then:
1. Create empty GitHub repo `RayhanXD/selfpi-demo-consumer`
2. Install the SelfPI GitHub App on it
3. `cd demo-consumer && git push -u origin main`
4. `make reset` (or restart API) → Bump → Open PR

Seed points `repo` / `repo_path` at that consumer when the folder exists.

Without these env vars, the pipeline detects call sites but does **not** open a PR. With them set, bump/check auto-open PRs when call sites exist, and Change Detail shows **Open PR**.

1. Create a [GitHub App](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps) with permissions:
   - **Contents:** Read & write
   - **Pull requests:** Read & write
   - **Metadata:** Read-only
2. Generate a private key (`.pem`). Install the App on a test repo that contains Stripe Python call sites (or push `fixtures/sample_repo`).
3. In `backend/.env`:

```bash
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
# Optional local-demo fallback only — leave empty for public Install App onboarding
# GITHUB_APP_INSTALLATION_ID=
# Optional; otherwise fetched from GET /app
# GITHUB_APP_SLUG=selfpi
GITHUB_DEFAULT_BASE_BRANCH=

# Login with GitHub (production)
GITHUB_CLIENT_ID=Iv1.xxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxx
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/auth/github/callback
FRONTEND_URL=http://localhost:5173
SESSION_SECRET=long-random-string
AUTH_REQUIRED=true
```

PEM newlines can be literal multiline or escaped `\n`.

On the GitHub App settings page also set:
- **Callback URL:** `http://localhost:8000/auth/github/callback` (must match `GITHUB_OAUTH_REDIRECT_URI`)
- **Setup URL:** `http://localhost:8000/auth/github/installed` (Install App returns here with `installation_id`)
- Generate a **Client secret** (Client ID is shown on the App’s General page)
- Make the App **public** if strangers should install it

4. Point the watched API’s `repo` field at `owner/name` via Settings → Connect (after login + install). Optionally set `REPO_PATH` to a local checkout for scanning.

5. Restart the API, run `make reset`, **Bump spec** on the demo API, open the change, click **Open PR** (or rely on auto-open when the App is configured).

### Login → Install → Connect

1. Open **Settings**
2. **Login with GitHub**
3. **Install SelfPI on GitHub** → pick repos → GitHub redirects back (`/auth/github/installed`)
4. Pick a repo → **Connect repo**
5. SelfPI **auto-detects APIs** from the local checkout (`repo_path` / `REPO_PATH` / `demo-consumer`). v1: **Python + Stripe** only — when Stripe is found, a live watched `stripe` API is ensured so the scheduler can poll it.

Try it: bootstrap `demo-consumer/` (`python3 scripts/bootstrap_demo_consumer.py`), connect that GitHub repo (or any connect with `REPO_PATH` / `demo-consumer` present) → response includes `detected_apis: ["stripe"]`.

Endpoints: `GET /auth/github/login`, `GET /auth/github/callback`, `GET /auth/github/install`, `GET /auth/github/installed`, `POST /auth/github/sync-installation`, `GET /auth/me`, `POST /auth/logout`, plus `/repos/*` including `POST /repos/connected/detect` (see `docs/API_CONTRACT.md`).

When OAuth is configured and `AUTH_REQUIRED=true`, `/repos/*` returns `401` until the user is signed in. Installation tokens open PRs; OAuth identifies the human and discovers their installation.

### Scheduled watcher

The API process runs a background poller that calls the same live check path as **Check now** (`poll_api`) for every `mode: "live"` API with a `spec_url`. Demo APIs are never auto-polled.

In `backend/.env`:

```bash
WATCH_ENABLED=true
WATCH_INTERVAL_SECONDS=300   # default 300 (5 minutes); minimum effective sleep is 5s
```

Set `WATCH_ENABLED=false` to disable (tests do this automatically). Logs look like:

```
watch poll starting: 1 live api(s), open_pr=True
watch poll stripe: no change
watch poll finished: checked=1 changed=0 failed=0
```

PRs open only when GitHub is configured **and** call sites exist (same flags as manual check/bump).

## Backend (manual)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # set MONGODB_URI + optional GitHub App
python -m db.seed      # seed stripe-demo + stripe
# python -m db.reset   # wipe + re-seed
uvicorn api.main:app --reload --port 8000
```

## Frontend (manual)

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /apis, /changes to :8000)
```

## Milestone status

| Milestone | Status |
|-----------|--------|
| **M0** Skeleton & data layer | Done |
| **M1** Diff engine | Done |
| **M2** Scanner core (Python) | Done |
| **M3** Adjudicator + Patcher | Done |
| **M4** REST API (pipeline wired) | Done |
| **M5** Frontend screens | Done |
| **M6** Demo loop + GitHub PR path | Done (configure App for live PRs) |

## GitHub

https://github.com/RayhanXD/SelfPI.git
