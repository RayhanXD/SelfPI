# Self-Maintaining APIs — Design Doc

*Working title: an agent that watches upstream API specs, finds affected call sites in your code, and opens a PR that fixes them — "Dependabot for APIs."*

Status: design / pre-build. Inspired by the YC Fall 2026 RFS "Self-Maintaining APIs."

---

## 1. The problem

Companies depend on third-party APIs (Stripe, Twilio, GitHub, …). When a vendor ships a **breaking change** — a removed field, renamed parameter, changed type — the notice arrives as an email or changelog that nobody reads. Weeks later, production breaks. The person who owned that integration has often left. (The RFS author notes ~30% of AWS service downtime came from unnoticed external API/package changes.)

**The product:** the day a vendor publishes a breaking change, detect it, find every affected call site in the customer's repo, and open a PR with the fix — before anyone gets paged.

---

## 2. Scope

**v1 (buildable slice):**

- One API: **Stripe.**
- One language: **Python.**
- One target repo (an app the developer already controls).
- A **self-hosted spec** the developer bumps on demand, so a breaking change is a button press, not an external wait — this doubles as the end-to-end integration test.
- Validate against **one real historical Stripe change** for a credible demo/screenshot.

**Later:** more languages, more APIs, prose-changelog handling, data-flow precision.

---

## 3. Pipeline

```
Vendor API Spec  (self-hosted, or real historical)
      │
      ▼
Spec Watcher     polls on a schedule
      │
      ▼
Diff Engine      detects breaking changes            [deterministic]
      │
      ▼
Scanner          finds affected call sites            [custom — see §5]
      │
      ▼
Patch Agent      writes the fix                       [LLM]
      │
      ▼
GitHub PR        opens on the repo, tests run
      │
      ▼
Dashboard        watched APIs · change feed · PR status
```

**Color of trust:** the deterministic stages (diff engine, scanner tiers 1–2) are unit-tested with exact assertions. The LLM stages (agent adjudication, patch) are tested at the **outcome** level — does the patched repo still compile and pass its own tests.

---

## 4. Why we build our own scanner

We deliberately do **not** use tree-sitter, Semgrep, or CodeQL as the core:

- **Vector search** — wrong tool. Finding a known symbol is an exact-match problem, not a similarity problem; embeddings can *silently* rank a real call site below the cutoff, which is the one failure a trust tool can't afford. (Kept as an optional triage lane for prose-only changelogs — see §8.)
- **CodeQL** — too heavy: needs to build the repo, is minutes-slow, and is commercially restricted. Reserved as a "data-flow precision" upgrade path.
- **tree-sitter / Semgrep** — solid, but wiring up a library isn't the point. The creative, resume-worthy work is designing our own representation and matcher.

The trick that keeps this **buildable**: work at the **token level**, not full-grammar parsing. More structure-aware than grep, far less work than a parser, fully ours, and deterministic/testable.

---

## 5. The scanner (custom, home-grown)

Four owned layers plus an agent adjudicator:

1. **Pre-filter (ripgrep)** — narrows a big repo to candidate files in ms. A recall net: guarantees we never skip a file that mentions the changed symbol.
2. **Tokenizer (ours)** — lexes each candidate into a token stream (identifiers, dots, parens, strings, comments). Because we know which tokens are in comments/strings, we ignore them — killing grep's biggest false-positive source. Per-language lexing quirks live in that language's module.
3. **Normalize to the Call-Site IR (§6)** — the creative core. One language-agnostic record shape for "an object, a member chain, invoked with arguments."
4. **Query + multi-signal scorer** — a small DSL compiled from the diff runs against the IR; a scorer combines signals into a confidence (exact token hit +, correct import present +, arg match +, in-comment −). High confidence → auto-include; low → adjudicate.
5. **Agent adjudication** — the LLM judges **only** the gray-zone records the deterministic layers already found. It confirms or rejects; it never hunts on its own. This keeps recall in the testable layers and keeps the agent cheap and bounded.

> **Known ceiling (accepted trade):** token-level matching does not do cross-statement **data flow** (e.g. `chg = create(); … chg.source` many lines later). The upgrade path is an AST/CodeQL layer for languages that need it. Deliberately out of v1.

---

## 6. The Call-Site IR (the creative core)

A normalized, language-agnostic record for every call site.

```
CallSite {
  // identity & location
  id            // stable hash of file + span
  file          // "billing.py"
  span          // { start_line, end_line, start_col, end_col }
  language      // "python"

  // shape of the call — what queries match against
  receiver      // "stripe"              (root object / namespace)
  path          // ["Charge", "create"]  (ordered member-access chain)
  invoked       // true → call();  false → field/attr access
  args: [
    { name: "source", value: "\"tok_123\"", value_kind: "literal",
      kind: "keyword", pos: 0 }
    // positional args: name = null, kind = "positional"
    // dynamic values: value_kind = "dynamic", value = expression text
  ]

  // semantic resolution
  operation_id  // "createCharge"  (canonical; see Decision 1)
  import        // { module: "stripe", symbol: null }
  alias         // "s" if `import stripe as s`, else null

  // scorer signals
  in_comment    // bool
  in_string     // bool
  in_test_file  // bool

  // display + agent
  snippet       // raw source of the call
  source_layer  // "grep" | "structural" | "agent"
  confidence    // 0.0–1.0
}
```

**One operation, three surfaces, one shape:**

```
# Python
stripe.Charge.create(source="tok_123")
→ receiver:"stripe" path:["Charge","create"] invoked:true
  args:[{name:"source", kind:"keyword"}]  operation_id:"createCharge"

// JavaScript
stripe.charges.create({ source: "tok_123" })
→ receiver:"stripe" path:["charges","create"] invoked:true
  args:[{name:"source", kind:"object-field"}] operation_id:"createCharge"

// Go
stripe.Charges.New(&stripe.ChargeParams{ Source: "tok_123" })
→ receiver:"stripe" path:["Charges","New"] invoked:true
  args:[{name:"Source", kind:"struct-field"}] operation_id:"createCharge"
```

A single query written against `operation_id` matches all three.

**Sequencing:** define the full schema now; **populate incrementally.** Start with `receiver`, `path`, `invoked`, `args[].name`, location, `in_comment` for Python. Add JavaScript next specifically to stress-test that the abstraction is truly language-agnostic — if adding JS forces a schema change, that's a finding; if a Python-written query "just works" on JS records, the IR is right.

---

## 7. Key design decisions

### Decision 1 — Operation vocabulary: **canonical operation IDs (chosen)**

The same operation has different SDK method names per language. Two options:

- **A. Query carries per-language surface names.** Simple to match, but every query bloats with language spellings and adding a language means editing all existing queries. Doesn't scale.
- **B. Canonical operation IDs + per-language resolver tables (CHOSEN).** Each operation gets one canonical ID (ideally the OpenAPI `operationId`). Each language module maps `surface name → operation_id`. A resolution pass tags every CallSite with `operation_id`. Breaking-change queries are written **once**, against the operation, not the spelling.

Why B: queries are language-agnostic and authored once; adding a language = adding one mapping table (existing queries untouched); it lines up with the OpenAPI spec the diff engine already reads; and it's a lightweight *semantic resolution* layer (the same idea CodeQL/LSP do, via a lookup table instead of a compiler). Cost — building the surface→canonical tables — is real but isolated in the language module as data, and often semi-derivable from the SDK's own generation.

Note: for a Python-only v1, A and B feel identical. Bake `operation_id` into the IR now; the weight only appears at language #2.

### Decision 2 — Argument capture: **capture values (chosen)**

Capture the argument value **as written**, not evaluated:

- Literal (`"card"`) → stored verbatim → high-confidence match against value-level breaking changes ("the `card` value is deprecated").
- Variable / expression (`customer_card`) → stored as expression text, marked `value_kind: "dynamic"` → routed to the agent to judge.

This gives arguments a natural confidence gradient that feeds the scorer directly.

### Decision 3 — Import & alias tracking: **yes (chosen)**

A per-file **pre-pass** walks import statements first and builds a binding table (`s → stripe`) so call sites emitted afterward resolve aliases (`import stripe as s`). This is the one place we rise slightly above pure token-matching; it's a large precision win and populates the IR's `import` / `alias` fields.

---

## 8. Data model (MongoDB Atlas)

MongoDB is the persistence layer (see §13). The data has a natural document shape: a **Change** document that *embeds* its call sites and PR status, so the API → change → call-sites → PR chain needs **no joins**. Atlas also supports ad-hoc queries and rich secondary indexes, so cross-API queries are normal `find`s rather than index puzzles. And OpenAPI specs are JSON, so spec snapshots live natively in the DB — no separate blob store.

### Collections

**`apis`** — one doc per watched API.

```json
{
  "_id": "stripe",
  "name": "Stripe",
  "spec_url": "https://.../openapi.json",
  "current_version": "2026-07-01",
  "status": "breaking_change_unhandled",   // up_to_date | change_detected | breaking_change_unhandled
  "languages": ["python"],
  "last_checked": "2026-07-26T09:00:00Z"
}
```

**`spec_versions`** — every fetched spec, versioned (this is what replaces S3). JSON-native.

```json
{
  "_id": "ObjectId",
  "api_id": "stripe",
  "version": "2026-07-01",
  "fetched_at": "2026-07-01T00:00:00Z",
  "spec": { "openapi": "3.1.0", "paths": { } }
}
```

Index: `{ api_id: 1, version: -1 }` — pull any two versions to re-run a diff.

**`changes`** — the core document; embeds call sites + PR.

```json
{
  "_id": "ObjectId",
  "api_id": "stripe",
  "operation_id": "createCharge",
  "kind": "renamed_param",      // removed_field | renamed_param | type_changed | value_deprecated
  "detail": { "param": "source", "replacement": "payment_method" },
  "from_version": "2026-06-01",
  "to_version": "2026-07-01",
  "detected_at": "2026-07-01T00:05:00Z",
  "repo": "myorg/billing-app",
  "status": "pr_open",          // detected | scanning | pr_open | merged | dismissed

  "call_sites": [               // embedded — always read together with the change
    {
      "file": "billing.py",
      "span": { "start_line": 12, "end_line": 12 },
      "language": "python",
      "receiver": "stripe",
      "path": ["Charge", "create"],
      "invoked": true,
      "operation_id": "createCharge",
      "args": [
        { "name": "source", "value": "\"tok_123\"", "value_kind": "literal", "kind": "keyword" }
      ],
      "import": { "module": "stripe", "symbol": null },
      "alias": null,
      "in_comment": false,
      "snippet": "stripe.Charge.create(source=\"tok_123\")",
      "source_layer": "structural",
      "confidence": 0.92
    }
  ],

  "pr": {                       // embedded
    "number": 42,
    "url": "https://github.com/myorg/billing-app/pull/42",
    "state": "open",            // open | merged | closed
    "tests_passing": true,
    "opened_at": "2026-07-01T00:10:00Z"
  }
}
```

**`changelog_chunks`** *(optional — the vector-search lane, §9)* — for APIs with prose-only changelogs.

```json
{ "api_id": "stripe", "text": "…release note…", "embedding": [/* e.g. 1536 floats */] }
```

with an Atlas **Vector Search** index on `embedding`.

### Access patterns → indexes

| Dashboard need | Query | Index |
|---|---|---|
| Changes for an API, newest first | `find({api_id}).sort({detected_at:-1})` | `{api_id:1, detected_at:-1}` |
| Call sites for a change | single doc read (embedded) | — |
| Change + its PR | single doc read (embedded) | — |
| **All unhandled changes across every API** | `find({status:"breaking_change_unhandled"})` | `{status:1, detected_at:-1}` |
| Watched APIs + status | `find()` on `apis` | — |
| Call sites by confidence | sort embedded array client-side (small set) | — |

The query that was *hard* in DynamoDB — "all unhandled across every API" — is a one-line indexed `find` here. Call sites embed cleanly: a change has at most dozens, far under Mongo's 16MB document limit.

---

## 9. Optional / future

- **Prose-changelog triage (the legitimate home for vector search):** some APIs publish no clean spec, only human-written release notes. Embed the changelog + code to *rank which files are worth parsing*, then hand off to the precise layers. Fuzzy input, fuzzy triage — never the exact-match core.
- **Data-flow precision:** add an AST or CodeQL-style layer for languages/changes that need cross-statement reasoning.
- **More languages / APIs:** each new language = a module (lexing rules + surface→operation_id table + query patterns).
- **Auto-derive mapping tables** from SDK generation metadata.

---

## 10. Language module (the extensibility unit)

Adding a language = adding one module containing:

- **Lexing rules** — comment syntax, string delimiters, identifier rules.
- **Surface → operation_id map** — the vocabulary table for Decision 1.
- **Query/emit patterns** — how this language's call shapes map into the IR.

"Add a language = add a module" is the extensibility pitch — and every layer underneath is code we wrote.

---

## 11. Testing strategy

- **Diff engine** — pure function; fixtures of `old spec / new spec / expected breaking changes`.
- **Tokenizer + IR** — input code → assert exact CallSite records (file, line, path, args).
- **Query + scorer** — input IR → assert matched records and confidence.
- **Agent adjudication + patch** — outcome tests: run against sample {breaking change + repo}; assert the patched repo compiles and its existing tests pass.

The whole self-hosted-spec demo loop *is* the end-to-end integration test.

---

## 12. Frontend (visibility layer)

The dashboard is where the work becomes *visible* — and for a resume project it's the part reviewers actually see, so it should expose the pipeline's internals, not just the outcome.

- **Watched APIs** — overview with status dots: up to date / change detected / breaking change unhandled.
- **Change feed** — timeline of detected changes ("Stripe · deprecated `source` on `createCharge` · 3 call sites · PR #42 open").
- **Change detail (the money screen)** — three panels side by side: the spec diff (old vs new), the affected call sites (files + highlighted lines), and the generated PR preview.
- **Call-Site Explorer (the distinctive screen)** — render the IR records with their confidence scores and which layer found each (grep / structural / agent). Turns the invisible scanner into something you can show — "here's my engine's reasoning, not a black box." Best demo moment.
- **PR status** — open / merged / tests passing.

---

## 13. Suggested stack

- **Frontend:** React + TypeScript, Tailwind, a diff-viewer component; renders the screens in §12.
- **Backend:** Python (pairs naturally with the LLM/agent work).
- **Pre-filter:** ripgrep.
- **Scanner:** our own tokenizer + IR + query DSL + scorer.
- **Agent / patch:** an LLM API.
- **GitHub:** a GitHub App to read repos and open PRs.
- **Scheduling:** a cron/worker to poll specs.
- **Storage — MongoDB Atlas:**
  - **`changes` collection** — core documents embedding call sites + PR status, so the API → change → call-sites → PR chain needs no joins.
  - **`spec_versions` collection** — every fetched OpenAPI spec, stored JSON-native (no separate blob store); any two versions can be pulled to re-run a diff.
  - **Atlas Vector Search** — optional, for the prose-changelog triage lane (§9).
  - Chosen over DynamoDB: document embedding removes the join problem, and ad-hoc queries + secondary indexes make cross-API queries ("all unhandled changes") a one-line `find` instead of a GSI puzzle — while still being real NoSQL resume value.
- **Deploy (later):** containerized backend + a scheduled worker; not required for v1.

---

## Open questions

1. Where exactly does the pre-filter hand off to the tokenizer — file paths only, or matched line ranges + context?
2. Format of the language module — Markdown-with-config, or a typed config file the tokenizer reads?
3. First real historical Stripe change to validate against (pick one with a clean, well-documented deprecation).
