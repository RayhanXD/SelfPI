"""Ensure watched API documents exist for detected third-party APIs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from db.client import apis
from detector.catalog import catalog_ids, get_entry

# Do not touch the demo bump target.
DEMO_API_IDS = frozenset({"stripe-demo"})

# Back-compat export used by tests / seed docs.
STRIPE_API_ID = "stripe"
STRIPE_SPEC_URL = (
    "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_watched_api(
    api_id: str,
    *,
    repo: str,
    repo_path: str | None = None,
    languages: list[str] | None = None,
) -> str | None:
    """Create or update a live watched API from the catalog.

    Returns the api id ensured, or None if unknown / not watchable / demo id.
    Never touches stripe-demo. Does not invent a second id for an existing doc.
    """
    if api_id in DEMO_API_IDS:
        return None
    entry = get_entry(api_id)
    if entry is None or not entry.watchable:
        return None

    langs = languages or ["python"]
    fields: dict[str, Any] = {
        "name": entry.name,
        "mode": "live",
        "spec_url": entry.spec_url,
        "languages": langs,
        "repo": repo,
        "source": "detected",
    }
    if repo_path:
        fields["repo_path"] = repo_path

    existing = apis().find_one({"_id": api_id})
    if existing:
        # Preserve manual overrides of spec_url when source is manual.
        if existing.get("source") == "manual" and existing.get("spec_url"):
            fields.pop("spec_url", None)
            fields["source"] = "manual"
        apis().update_one({"_id": api_id}, {"$set": fields})
        return api_id

    apis().insert_one(
        {
            "_id": api_id,
            **fields,
            "current_version": None,
            "status": "up_to_date",
            "last_checked": None,
            "open_change_count": 0,
        }
    )
    return api_id


def ensure_stripe(*, repo: str, repo_path: str | None = None) -> str:
    """Back-compat — ensure live Stripe."""
    ensured = ensure_watched_api(STRIPE_API_ID, repo=repo, repo_path=repo_path)
    return ensured or STRIPE_API_ID


def detach_undetected(*, repo: str, detected: list[str]) -> list[str]:
    """Clear repo binding on catalog live APIs for this repo that were not detected.

    Keeps baselines/history; just unlinks so the dashboard for this repo is clean.
    Never touches demo APIs or source=manual docs.
    """
    detected_set = set(detected)
    known = catalog_ids()
    detached: list[str] = []
    for doc in apis().find({"mode": "live", "repo": repo}):
        api_id = str(doc["_id"])
        if api_id in DEMO_API_IDS:
            continue
        if api_id in detected_set:
            continue
        if doc.get("source") == "manual":
            continue
        if api_id not in known and doc.get("source") != "detected":
            continue
        apis().update_one(
            {"_id": api_id},
            {"$unset": {"repo": "", "repo_path": ""}},
        )
        detached.append(api_id)
    return detached


def ensure_watched_apis(
    detected: list[str],
    *,
    repo: str,
    repo_path: str | None = None,
    languages_by_api: dict[str, list[str]] | None = None,
) -> list[str]:
    """For each detected api id, ensure a live watched doc. Returns ensured ids."""
    ensured: list[str] = []
    for api_id in detected:
        langs = (languages_by_api or {}).get(api_id)
        got = ensure_watched_api(
            api_id, repo=repo, repo_path=repo_path, languages=langs
        )
        if got:
            ensured.append(got)
    detach_undetected(repo=repo, detected=detected)
    return ensured
