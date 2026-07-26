# CLAUDE.md — Repo Conventions

Guidance for anyone (human or agent) writing code in this repo. Keep it short and follow it.

## What this project is

Self-Maintaining APIs: watch an upstream API spec, detect breaking changes, find affected call sites in a repo, and open a PR that fixes them. See `docs/self-maintaining-apis-design.md` for the full design, `docs/PRD.md` for product scope, `docs/ENGINEERING_PLAN.md` for build order, `docs/API_CONTRACT.md` for endpoints, `docs/FRONTEND_GUIDELINES.md` for UI.

## Golden rules

1. **Recall is sacred.** The deterministic layers (prefilter, tokenizer, IR, query, scorer) must never *silently* drop a real call site. A surfaced false positive is fine; a silent false negative is a bug.
2. **Keep deterministic modules pure.** Diff, tokenizer, IR normalizer, query, and scorer are side-effect-free functions with fixture-based tests. No network, no DB, no LLM calls inside them.
3. **Bound the LLM.** The adjudicator only sees candidate records the deterministic layers already produced. It confirms or rejects — it never scans on its own.
4. **The IR is the contract.** All languages normalize to the same `CallSite` shape (design doc §6). If a new language forces a schema change, stop and discuss — that's a design signal.
5. **Extend by module, not by patching the core.** New language = new module under `backend/languages/`. Don't scatter language-specific logic through the pipeline.

## Structure

Monorepo per `docs/ENGINEERING_PLAN.md` §1: `backend/` (watcher, diff, scanner/*, patcher, api, db, languages), `frontend/`, `fixtures/`, `docs/`.

## Naming

- Data fields use `snake_case` everywhere (matches the Mongo docs and API contract).
- Status/enum values are exactly those in `docs/API_CONTRACT.md` — don't invent variants.
- Canonical API operations are referenced by `operation_id` (the OpenAPI operationId), never by SDK method name.

## Testing

- Every deterministic module ships with fixture tests (`old/new/expected` for diff; `code → expected CallSite[]` for scanner). Recall on scanner fixtures must be 100%.
- LLM modules (adjudicator, patcher) are tested by outcome: the patched sample repo compiles and its existing tests pass.
- Don't mark a task done with failing tests or a partial implementation.

## Backend

- Python. Deterministic core has no external calls. Isolate LLM and GitHub/network I/O in `adjudicator/` and `patcher/`.
- MongoDB access lives in `db/`; nothing else talks to Mongo directly. Call sites and PR are embedded in the change document — no joins.

## Frontend

- React + TypeScript + Tailwind. Dark-minimal only (no theme toggle in v1).
- Use the tokens in `docs/FRONTEND_GUIDELINES.md`; do not hardcode colors. One accent; status/confidence colors are semantic.
- Monospace for anything code-shaped (paths, symbols, JSON, diffs). Never encode meaning in color alone — pair with a label.

## Commits / PRs

- Small, focused commits; imperative messages ("add python tokenizer", not "added").
- A change to the IR schema or the API contract must update the corresponding doc in the same PR.

## When unsure

Prefer the choice that preserves recall and keeps deterministic layers testable. If a decision affects the IR, the operation-vocabulary mapping, or the API contract, check the design doc first and update docs alongside code.
