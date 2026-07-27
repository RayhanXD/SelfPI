# PRD — Self-Maintaining APIs

*Companion to `self-maintaining-apis-design.md` (the technical design). This doc is the product-level "what and why"; the design doc is the "how."*

Status: v1 pre-build. Owner: Rayhan.

---

## 1. Summary

An agent that watches upstream API specs, detects breaking changes, finds every affected call site in a connected repo, and opens a pull request that fixes them — before the change ever breaks production. "Dependabot for APIs."

## 2. Problem

Teams depend on third-party APIs. When a vendor ships a breaking change (removed field, renamed parameter, changed type, deprecated value), the notice arrives as a changelog or email nobody reads. Weeks later production breaks, often after the engineer who owned that integration has moved on. The work to detect, locate, and fix is manual, reactive, and usually happens during an incident.

## 3. Goals & non-goals

**Goals (v1)**

- Detect breaking changes in a watched API spec automatically.
- Locate affected call sites in one connected repo with high precision and, critically, high recall (never silently miss one).
- Open a PR with a proposed fix and a clear explanation.
- Give the user a dashboard that makes the whole process visible, including *why* each call site was flagged.

**Non-goals (v1)**

- Multi-language support beyond Python (architecture allows it; not shipped).
- Multiple APIs beyond a fixed catalog: v1 detects a growing set of known Python SDKs with public OpenAPI URLs (Stripe, OpenAI, Twilio, GitHub, …); unknown vendors need a manual OpenAPI URL. Call-site→operation maps are still richest for Stripe.
- Deep cross-statement data-flow analysis (known ceiling; documented upgrade path).
- Auto-merging PRs. A human always reviews.
- Handling APIs with no machine-readable spec (prose-changelog triage is a documented future lane).

## 4. Users & personas

- **Integration owner (primary):** the engineer responsible for a third-party integration. Wants to stop finding out about breaking changes from a production alert.
- **Eng lead / on-call:** wants fewer surprise incidents from upstream changes; wants an audit trail.
- **Solo/small team dev:** has no time to monitor vendor changelogs; wants it handled.

## 5. User stories (v1)

1. As an integration owner, I connect a GitHub repo and select an API to watch, so the system knows what to monitor.
2. As an integration owner, when the API ships a breaking change, I receive a PR that fixes the affected call sites, so I don't fix it by hand during an incident.
3. As an eng lead, I open the dashboard and see every watched API with a status, so I know at a glance what needs attention.
4. As an integration owner, I open a detected change and see the spec diff, the exact affected call sites, and the generated fix, so I can trust and review it.
5. As a skeptical reviewer, I can see *which layer* flagged each call site and its confidence, so I understand the tool's reasoning rather than trusting a black box.
6. As a developer, I can trigger a spec change on a self-hosted test API, so I can demo and validate the whole loop on demand.

## 6. Scope — v1 slice

- One connected repo; **auto-detect** known third-party APIs from the checkout (Python catalog — Stripe plus other public OpenAPI vendors). Stripe remains the deepest call-site/fix path.
- A **self-hosted spec** the user can bump to trigger a change on demand (also the end-to-end test harness).
- Validation against **one real historical Stripe breaking change**.

## 7. Core flow

1. User connects a repo and selects an API to watch.
2. Spec Watcher polls the API's spec on a schedule.
3. Diff Engine compares the new spec to the last stored version and detects breaking changes.
4. Scanner finds affected call sites (pre-filter → tokenize → IR → query → score → agent-adjudicate the gray zone).
5. Patch Agent writes a fix for the confirmed call sites.
6. A GitHub PR is opened; the repo's own tests run against it.
7. Dashboard reflects the change, the call sites, and the PR status throughout.

## 8. Requirements

**Functional**

- Poll and version-store API specs.
- Detect breaking-change kinds: removed field, renamed parameter, type change, deprecated value.
- Scan a repo and produce Call-Site records with confidence and provenance (which layer found it).
- Generate a PR with a human-readable explanation of what changed and what was fixed.
- Dashboard screens: Watched APIs, Change Feed, Change Detail, Call-Site Explorer, PR Status (see design doc §12).

**Non-functional**

- **Recall first:** the deterministic layers must not silently drop a candidate file. A false positive (surfaced for review) is acceptable; a silent false negative is not.
- **Deterministic where it counts:** diff engine, tokenizer, IR, query, and scorer are deterministic and unit-testable.
- **Bounded LLM use:** the agent only adjudicates candidates the deterministic layers already surfaced; it never scans the whole repo.
- **Observable:** every flagged call site carries its source layer and confidence for display.

## 9. Success criteria

- On the self-hosted test API, bumping the spec reliably produces a correct PR end-to-end.
- On one real historical Stripe change, the tool detects it, finds the known affected call sites, and opens a compiling PR whose changes pass the repo's tests.
- Scanner recall on the test fixtures = 100% of true call sites surfaced (precision can be < 100%, with the agent trimming false positives).
- A reviewer can explain, from the dashboard alone, why any given call site was flagged.

## 10. Risks & mitigations

- **Silent misses erode trust.** → Deterministic recall net (ripgrep) guarantees no file mentioning the symbol is skipped; recall is tested with fixtures.
- **Bad PRs erode trust.** → PRs are proposals, never auto-merged; the repo's tests gate them; the explanation makes review fast.
- **Vocabulary mismatch across SDKs.** → Canonical operation IDs with per-language resolver tables (design doc, Decision 1).
- **Scope creep into multi-language/multi-API too early.** → v1 is explicitly Python + Stripe; the second language is added only to validate the abstraction.

## 11. Open questions

Carried from the design doc: pre-filter→tokenizer handoff shape; language-module file format; which historical Stripe change to validate against.
