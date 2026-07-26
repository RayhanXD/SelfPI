# Engineering Plan — Self-Maintaining APIs

How to actually build the v1 slice (Stripe + Python + one repo). Read alongside the design doc for the "why."

---

## 1. Repo layout

Monorepo, two apps + shared types.

```
self-maintaining-apis/
├── backend/
│   ├── watcher/          # spec polling + version storage
│   ├── diff/             # breaking-change detection
│   ├── scanner/          # the custom engine (the heart)
│   │   ├── prefilter/    # ripgrep candidate-file finder
│   │   ├── tokenizer/    # per-language lexer
│   │   ├── ir/           # Call-Site IR types + normalizer
│   │   ├── query/        # DSL + matcher over the IR
│   │   ├── scorer/       # multi-signal confidence
│   │   └── adjudicator/  # bounded agent review of gray-zone records
│   ├── patcher/          # agent that writes the fix + opens PR
│   ├── api/              # REST layer (see API_CONTRACT.md)
│   ├── db/               # MongoDB access, collection schemas, indexes
│   └── languages/        # language modules (python.* first)
├── frontend/             # React + TS + Tailwind (dark-minimal)
├── fixtures/             # test specs, sample repos, golden IR records
└── docs/                 # design doc, PRD, this plan, API contract
```

## 2. Module contracts (build to these interfaces)

- **Watcher** → in: API config. out: new `spec_versions` doc when the spec changes.
- **Diff** → in: two spec versions. out: list of `BreakingChange { operation_id, kind, detail }`. *Pure function.*
- **Prefilter** → in: repo path + symbol/endpoint hints. out: candidate file paths (+ matched line ranges). *Deterministic.*
- **Tokenizer** → in: source file + language module. out: token stream. *Deterministic.*
- **IR normalizer** → in: token stream + import pre-pass. out: `CallSite[]`. *Deterministic.*
- **Query/matcher** → in: `CallSite[]` + a compiled query from a `BreakingChange`. out: matched `CallSite[]`. *Deterministic.*
- **Scorer** → in: matched `CallSite[]`. out: same records with `confidence` + `source_layer`. *Deterministic.*
- **Adjudicator** → in: gray-zone `CallSite[]`. out: confirmed/rejected. *LLM, bounded to inputs.*
- **Patcher** → in: confirmed `CallSite[]` + `BreakingChange`. out: a PR. *LLM + GitHub API.*

Keep every deterministic module a pure, side-effect-free function so it's trivially testable.

## 3. Build order (dependency-ordered milestones)

**M0 — Skeleton & data layer**
Repo scaffold, MongoDB Atlas connection, collection schemas + indexes (`apis`, `spec_versions`, `changes`), shared IR types. Seed one `apis` doc and one `spec_versions` doc.

**M1 — Diff engine (pure, testable first)**
Parse two OpenAPI specs, detect the four breaking-change kinds. Fixtures: `old.json / new.json / expected.json`. No UI yet. *This is the cleanest first win.*

**M2 — Scanner core, Python only**
Prefilter (ripgrep) → Python tokenizer → IR normalizer (with import pre-pass) → query → scorer. Output `CallSite[]` for a known change against the sample repo. Golden-record tests. *This is the heart; budget the most time here.*

**M3 — Adjudicator + Patcher**
Bounded agent over gray-zone records; patch agent generates the fix and opens a real PR on the sample repo via a GitHub App. Outcome test: patched repo compiles and its tests pass.

**M4 — REST API**
Wire the endpoints in `API_CONTRACT.md` over the pipeline + DB.

**M5 — Frontend**
Build the five screens (design doc §12) against the API, dark-minimal per the frontend guidelines. Prioritize Change Detail + Call-Site Explorer.

**M6 — Demo loop + real validation**
Self-hosted test spec with a "bump" button that triggers the full loop live. Then validate against one real historical Stripe change and capture the screenshot for the resume.

## 4. Testing strategy (mirrors design doc §11)

- Deterministic modules (diff, tokenizer, IR, query, scorer): exact unit tests from fixtures. Recall on scanner fixtures must be 100%.
- LLM modules (adjudicator, patcher): outcome tests — patched repo compiles + existing tests pass.
- End-to-end: the self-hosted-spec bump *is* the integration test.

## 5. Definition of done (v1)

- `spec bump → PR` works end-to-end on the test API.
- One real historical Stripe change detected, located, and fixed with a passing PR.
- All five dashboard screens functional; Call-Site Explorer shows layer + confidence.
- Deterministic layers have fixture-based tests; recall = 100% on fixtures.

## 6. Sequencing notes

- Build M1 and M2 **before** any UI — they're pure and give fast, testable wins.
- Add a **second language (JS)** only after M2 works, purely to stress-test that the IR is language-agnostic (design doc §6). Not part of v1 DoD.
- Defer auth beyond what the GitHub App requires; single-user is fine for v1.
