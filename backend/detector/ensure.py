"""Ensure watched API documents exist for detected third-party APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from db.client import apis

# Real Stripe OpenAPI (same URL as db.seed live stripe).
STRIPE_API_ID = "stripe"
STRIPE_SPEC_URL = (
    "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"
)

# Do not touch the demo bump target.
DEMO_API_IDS = frozenset({"stripe-demo"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stripe_fields(*, repo: str, repo_path: str | None) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "name": "Stripe",
        "mode": "live",
        "spec_url": STRIPE_SPEC_URL,
        "languages": ["python"],
        "repo": repo,
    }
    if repo_path:
        fields["repo_path"] = repo_path
    return fields


def ensure_stripe(*, repo: str, repo_path: str | None = None) -> str:
    """Create or update the live `stripe` watched API. Never touches stripe-demo.

    If `stripe` already exists, stamp/update it — do not invent a second id.
    Returns the api id ensured (`stripe`).
    """
    fields = _stripe_fields(repo=repo, repo_path=repo_path)
    existing = apis().find_one({"_id": STRIPE_API_ID})
    if existing:
        apis().update_one({"_id": STRIPE_API_ID}, {"$set": fields})
        return STRIPE_API_ID

    apis().insert_one(
        {
            "_id": STRIPE_API_ID,
            **fields,
            "current_version": None,
            "status": "up_to_date",
            "last_checked": None,
            "open_change_count": 0,
        }
    )
    return STRIPE_API_ID


def ensure_watched_apis(
    detected: list[str],
    *,
    repo: str,
    repo_path: str | None = None,
) -> list[str]:
    """For each detected api id, ensure a live watched doc. Returns ensured ids."""
    ensured: list[str] = []
    for api_id in detected:
        if api_id in DEMO_API_IDS:
            continue
        if api_id == STRIPE_API_ID:
            ensured.append(ensure_stripe(repo=repo, repo_path=repo_path))
    return ensured
