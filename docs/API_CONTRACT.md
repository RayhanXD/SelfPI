# API Contract — Self-Maintaining APIs

REST endpoints the frontend consumes. Lets frontend and backend be built in parallel against a stable shape. JSON over HTTP. All responses `application/json`.

Conventions: `snake_case` fields (match the MongoDB docs), ISO-8601 UTC timestamps, cursor/limit pagination where lists can grow. Errors: `{ "error": { "code": string, "message": string } }` with appropriate HTTP status.

---

## Watched APIs

### `GET /apis`
List watched APIs (Watched APIs screen).

Query: `scope=workspace` (default) | `scope=all`.

- `workspace` — when a repo is connected, only APIs whose `repo` matches that connection. The local `stripe-demo` API is included only when `INCLUDE_DEMO_APIS=true` **and** nothing is connected (or the connected repo is the demo consumer).
- `all` — every watched API doc (debug).

```json
[
  {
    "id": "openai",
    "name": "OpenAI",
    "current_version": null,
    "status": "up_to_date",
    "languages": ["python"],
    "last_checked": null,
    "open_change_count": 0,
    "mode": "live",
    "repo": "myorg/billing-app",
    "spec_url": "https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml"
  }
]
```

`mode` is `"demo"` (Bump spec) or `"live"` (Check now). Do not mix demo bumps with live polls on the same API id.

### `POST /apis`
Watch a new API.
Request: `{ "id": "stripe", "name": "Stripe", "spec_url": "https://.../openapi.json", "repo": "myorg/billing-app", "languages": ["python"] }`
Response: the created API object (as above).

### `GET /apis/{id}`
Single API detail. Same shape as list item.

### `POST /apis/{id}/check`
Manually trigger a spec poll now ("Check now" button). Response:

```json
{
  "checked": true,
  "new_version": "2026-07-01",
  "changes_detected": 0,
  "baseline": true
}
```

- `new_version` is the stored version string when the fetched fingerprint differs from the latest stored version; otherwise `null` (no store).
- `changes_detected` is the number of breaking-change docs created for this poll.
- `baseline: true` means this was a **first-run (or live re-)baseline**: the spec was stored, but breaking-change detection was skipped (`changes_detected` is always `0`). Live APIs (`mode: "live"`) only diff full-spec-to-full-spec — a tiny/demo prior accidentally attached to a live API is treated as no baseline and replaced quietly. Subsequent polls that differ from a real baseline create changes as usual (`baseline: false`).

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
  "connected_repo": "myorg/billing-app",
  "watch_interval_seconds": 300,
  "watch_enabled": true,
  "oauth_configured": true,
  "login_required": true,
  "authenticated": true,
  "user": { "id": 1, "login": "octocat", "name": "Mono", "avatar_url": "…", "html_url": "…" },
  "login_url": "/auth/github/login",
  "app_installed": false,
  "install_url": "https://github.com/apps/selfpi/installations/new",
  "hint": "Install SelfPI on GitHub, then connect a repository."
}
```

`github_configured` is true when the server has `GITHUB_APP_ID` + private key. `app_installed` is true when an installation id is known (session, connected workspace, or optional `GITHUB_APP_INSTALLATION_ID` env fallback). `connected_repo` is the workspace binding from `POST /repos/connect` (or `null`). `watch_*` describe the background live-API poller.

---

## Auth (Login with GitHub)

GitHub App **user-to-server OAuth**. Requires `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and a Callback URL on the App matching `GITHUB_OAUTH_REDIRECT_URI`.

For public onboarding set the App **Setup URL** to `{API}/auth/github/installed` so Install App returns with `installation_id`.

### `GET /auth/github/login`
Redirects the browser to GitHub’s authorize URL. Sets a short-lived `selfpi_oauth_state` cookie.

### `GET /auth/github/callback`
Exchanges `code` for a user token, loads `/user`, discovers this App’s installation via `GET /user/installations`, sets httponly `selfpi_session` cookie, redirects to `{FRONTEND_URL}/auth/callback?auth=ok` (or `auth=error`).

In production (`ENV=production` or HTTPS `FRONTEND_URL`), session and OAuth state cookies use `Secure` + `SameSite=None` so a cross-origin Vercel frontend can call the API with `credentials: include`. Locally they use `SameSite=Lax` without `Secure`.

### `GET /auth/github/install`
Redirects to `https://github.com/apps/{slug}/installations/new` (slug from `GITHUB_APP_SLUG` or `GET /app`).

### `GET /auth/github/installed`
GitHub Setup URL target after Install / Update (`?installation_id=&setup_action=`). Stores `installation_id` on the session and redirects to `{FRONTEND_URL}/settings?installed=1`.

### `POST /auth/github/sync-installation`
Re-runs installation discovery for the signed-in user and refreshes the session cookie.

```json
{ "app_installed": true, "install_url": "https://github.com/apps/selfpi/installations/new", "installation_id": "149236841" }
```

### `GET /auth/me`
```json
{
  "authenticated": true,
  "oauth_configured": true,
  "login_required": true,
  "user": { "id": 1, "login": "octocat", "name": "Mono", "avatar_url": "…", "html_url": "…" },
  "login_url": "/auth/github/login",
  "app_installed": true,
  "install_url": "https://github.com/apps/selfpi/installations/new"
}
```

### `POST /auth/logout`
Clears the session cookie. `{ "logged_out": true }`.

When `AUTH_REQUIRED=true` and OAuth is configured, `/repos/*` returns `401 login_required` until the user is signed in.

---

## Connected repo (GitHub App)

Lists repos via the **installation token** for the user’s installation (session → connected workspace → optional env fallback). Connecting a repo requires Login with GitHub when OAuth is configured.

### `GET /repos`
List repositories accessible to the configured App installation.

```json
{
  "items": [
    {
      "full_name": "myorg/billing-app",
      "owner": "myorg",
      "name": "billing-app",
      "private": false,
      "default_branch": "main",
      "html_url": "https://github.com/myorg/billing-app",
      "connected": true
    }
  ],
  "connected_repo": "myorg/billing-app"
}
```

Errors: `503` if the App is not configured, `502` if GitHub rejects the request.

### `GET /repos/connected`
Current connected repo, or `null`.

```json
{
  "full_name": "myorg/billing-app",
  "owner": "myorg",
  "name": "billing-app",
  "default_branch": "main",
  "html_url": "https://github.com/myorg/billing-app",
  "private": false,
  "repo_path": "/optional/local/checkout",
  "connected_at": "2026-07-26T21:00:00Z"
}
```

### `POST /repos/connect`
Bind a repo as the workspace target. Request: `{ "full_name": "myorg/billing-app", "repo_path": "/optional/local/checkout" }`.

When the App is configured, `full_name` must appear in `GET /repos`. Does **not** stamp every watched API onto the new repo (avoids attaching `stripe-demo` / seeded leftovers). Detection stamps only matched catalog APIs.

After connect succeeds, SelfPI **auto-detects third-party APIs** from the local checkout (`repo_path` → `REPO_PATH` → `demo-consumer/` when present) using the Python catalog in `backend/detector/catalog.py` (Stripe, OpenAI, Twilio, GitHub, Slack, Discord, Plaid, Square, Anthropic, …). Matching is recall-first on `import` / `from` and dependency manifests. For each **watchable** hit (has a public OpenAPI URL), ensures a live watched API with that id. Catalog hits without a spec URL are returned in `unwatchable` and are not ensured. Undetected catalog APIs previously bound to this repo are detached (repo cleared). Never removes `stripe-demo`.

Response: connected repo object plus `detected_apis` / `unwatchable`:

```json
{
  "full_name": "myorg/billing-app",
  "owner": "myorg",
  "name": "billing-app",
  "default_branch": "main",
  "html_url": "https://github.com/myorg/billing-app",
  "private": false,
  "repo_path": "/optional/local/checkout",
  "connected_at": "2026-07-26T21:00:00Z",
  "detected_apis": ["openai", "stripe"],
  "unwatchable": []
}
```

### `POST /repos/connected/detect`
Re-run API detection on the connected repo checkout and ensure matching live watched APIs. Requires a connected repo (`404` with `no_connected_repo` otherwise).

```json
{
  "detected_apis": ["openai", "stripe"],
  "ensured": ["openai", "stripe"],
  "unwatchable": [],
  "repo_path": "/optional/local/checkout",
  "full_name": "myorg/billing-app"
}
```

### `DELETE /repos/connected`
Clear the connected-repo binding. Response: `{ "disconnected": true }`. Does not wipe watched API `repo` fields (re-connect to change them).

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
- Auth in v1: Login with GitHub + Install App onboarding. Server keeps App credentials (`GITHUB_APP_ID` / private key / OAuth client). Strangers install the App from Settings; `installation_id` lives on the session and connected-repo document. Optional `GITHUB_APP_INSTALLATION_ID` is a single-tenant / local-demo fallback only.
- The scheduled watcher polls only `mode: "live"` APIs with a `spec_url` (never demo bumps). Interval: `WATCH_INTERVAL_SECONDS` (default 300). Disable with `WATCH_ENABLED=false`.
