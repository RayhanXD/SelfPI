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
- MongoDB (local or Atlas)

## Backend (M0)

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

## Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /apis, /changes to :8000)
```

## Milestone status

| Milestone | Status |
|-----------|--------|
| **M0** Skeleton & data layer | Scaffolded |
| M1 Diff engine | Stub + fixtures ready |
| M2 Scanner core (Python) | Module stubs + sample repo |
| M3 Adjudicator + Patcher | Stubs |
| M4 REST API (full pipeline) | Contract routes live; pipeline not wired |
| M5 Frontend screens | Shell + five screens against API |
| M6 Demo loop | Pending |

## GitHub

https://github.com/RayhanXD/SelfPI.git
