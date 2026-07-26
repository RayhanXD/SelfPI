# API Contract — Self-Maintaining APIs

REST endpoints the frontend consumes. Lets frontend and backend be built in parallel against a stable shape. JSON over HTTP. All responses `application/json`.

Conventions: `snake_case` fields (match the MongoDB docs), ISO-8601 UTC timestamps, cursor/limit pagination where lists can grow. Errors: `{ "error": { "code": string, "message": string } }` with appropriate HTTP status.

---

## Watched APIs

### `GET /apis`
List watched APIs (Watched APIs screen).

```json
[
  {
    "id": "stripe-demo",
    "name": "Stripe (demo)",
    "current_version": "2026-06-01",
    "status": "up_to_date",
    "languages": ["python"],
    "last_checked": "2026-07-26T09:00:00Z",
    "open_change_count": 0,
    "mode": "demo",
    "repo": "myorg/billing-app"
  }
]
```

`mode` is `"demo"` (Bump spec) or `"live"` (Check now). Do not mix demo bumps with live Stripe polls on the same API id.

### `POST /apis`
Watch a new API.
Request: `{ "id": "stripe", "name": "Stripe", "spec_url": "https://.../openapi.json", "repo": "myorg/billing-app", "languages": ["python"] }`
Response: the created API object (as above).

### `GET /apis/{id}`
Single API detail. Same shape as list item.

### `POST /apis/{id}/check`
Manually trigger a spec poll now ("Check now" button). Response: `{ "checked": true, "new_version": "2026-07-01" | null, "changes_detected": 1 }`.

---

## Changes

### `GET /changes`
Change feed. Query params: `api_id?`, `status?` (e.g. `breaking_change_unhandled`), `limit?`, `cursor?`.

```json
{
  "items": [
    {
      "id": "665f...",
      "api_id": "stripe",
      "operation_id": "createCharge",
      "kind": "renamed_param",
      "detail": { "param": "source", "replacement": "payment_method" },
      "call_site_count": 3,
      "status": "pr_open",
      "pr": { "number": 42, "state": "open", "tests_passing": true },
      "detected_at": "2026-07-01T00:05:00Z"
    }
  ],
  "next_cursor": null
}
```

### `GET /changes/{id}`
Full change detail (Change Detail + Call-Site Explorer). Includes embedded call sites and PR, plus the spec diff for the affected operation.

```json
{
  "id": "665f...",
  "api_id": "stripe",
  "operation_id": "createCharge",
  "kind": "renamed_param",
  "detail": { "param": "source", "replacement": "payment_method" },
  "from_version": "2026-06-01",
  "to_version": "2026-07-01",
  "status": "pr_open",
  "repo": "myorg/billing-app",
  "spec_diff": {
    "operation_id": "createCharge",
    "removed": ["source"],
    "added": ["payment_method"],
    "raw": "<unified diff string for the operation>"
  },
  "call_sites": [
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
  "pr": {
    "number": 42,
    "url": "https://github.com/myorg/billing-app/pull/42",
    "state": "open",
    "tests_passing": true,
    "opened_at": "2026-07-01T00:10:00Z"
  },
  "detected_at": "2026-07-01T00:05:00Z"
}
```

### `POST /changes/{id}/dismiss`
Mark a change as handled/ignored. Response: updated change summary.

### `POST /changes/{id}/rescan`
Re-run the scanner for this change (e.g., after repo updates). Response: `{ "call_site_count": 3, "status": "scanning" }`.

### `POST /changes/{id}/open-pr`
Open a fix PR for this change via the GitHub App. Requires call sites and configured `GITHUB_APP_*` env vars. Response: updated change summary with `status: "pr_open"` and embedded `pr`. Errors: `503` if the App is not configured, `400` if there are no call sites, `502` if GitHub rejects the request.

---

## Settings

### `GET /settings`
Public config for the Settings screen (no secrets).

```json
{
  "github_configured": false,
  "default_base_branch": "main",
  "repo_path_set": false,
  "hint": "Set GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, and GITHUB_APP_INSTALLATION_ID in backend/.env — see README."
}
```

---

## Specs (for the diff/demo loop)

### `GET /apis/{id}/spec-versions`
List stored spec versions (for re-running diffs / the demo). `[{ "version": "2026-07-01", "fetched_at": "..." }, ...]`.

### `POST /apis/{id}/spec-versions` *(test/demo only)*
Manually push a new spec version to the self-hosted test API — the "bump" button that triggers the loop on demand. Request: `{ "version": "2026-07-02", "spec": { ...OpenAPI... } }`. Response: `{ "version": "2026-07-02", "changes_detected": 1 }`.

---

## Status enums (shared with frontend)

```
api.status:    up_to_date | change_detected | breaking_change_unhandled
change.status: detected | scanning | pr_open | merged | dismissed
change.kind:   removed_field | renamed_param | type_changed | value_deprecated
call_site.source_layer: grep | structural | agent
pr.state:      open | merged | closed
```

## Notes

- `call_sites` are embedded in the change document (Mongo), so `GET /changes/{id}` needs no join.
- The confidence→color mapping and layer badges are a frontend concern (see FRONTEND_GUIDELINES §2).
- Auth in v1 is minimal (single user); endpoints assume the GitHub App is already installed on the connected repo.
