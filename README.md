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
  Atlas works too once Network Access allows your IP (`0.0.0.0/0` for dev).

## Run everything

```bash
make
```

- UI:  http://localhost:5173 — open Watched APIs → **Bump spec**
- API: http://localhost:8000/health

`make stop` kills API, UI, and local mongod.

## Backend (manual)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # set MONGODB_URI
python -m db.seed      # seed Stripe api + spec_versions
uvicorn api.main:app --reload --port 8000
```

Health: `GET http://localhost:8000/health`

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
| **M6** Demo loop + Stripe validation | Pending |

## GitHub

https://github.com/RayhanXD/SelfPI.git
