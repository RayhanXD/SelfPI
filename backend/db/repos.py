"""Connected GitHub repo — single-user v1 workspace binding."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from db.client import apis, repos

CONNECTED_ID = "connected"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_connected_repo() -> dict[str, Any] | None:
    """Return the connected repo document, or None."""
    doc = repos().find_one({"_id": CONNECTED_ID})
    if not doc:
        return None
    return doc


def connect_repo(
    *,
    full_name: str,
    owner: str | None = None,
    name: str | None = None,
    default_branch: str | None = None,
    html_url: str | None = None,
    private: bool | None = None,
    repo_path: str | None = None,
    installation_id: str | None = None,
    propagate_to_apis: bool = False,
    propagate_api_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Persist the connected repo and optionally stamp it onto watched APIs.

    By default does **not** stamp every watched API (avoids attaching stripe-demo
    / seeded leftovers to an unrelated connected repo). Pass
    `propagate_api_ids` for the detected set, or `propagate_to_apis=True` to
    stamp all docs (legacy).
    """
    full_name = full_name.strip()
    if "/" not in full_name:
        raise ValueError("full_name must be owner/name")
    parsed_owner, parsed_name = full_name.split("/", 1)
    owner = (owner or parsed_owner).strip()
    name = (name or parsed_name).strip()
    if not owner or not name:
        raise ValueError("full_name must be owner/name")

    existing = get_connected_repo()
    resolved_installation = installation_id or (existing or {}).get("installation_id")
    full = f"{owner}/{name}"

    # When switching to a different GitHub repo, drop the previous local path
    # so we don't keep scanning demo-consumer for C.Y.R.U.S. (etc.).
    if repo_path is not None:
        resolved_path = repo_path
    elif existing and existing.get("full_name") == full:
        resolved_path = existing.get("repo_path")
    else:
        resolved_path = None

    doc: dict[str, Any] = {
        "_id": CONNECTED_ID,
        "full_name": full,
        "owner": owner,
        "name": name,
        "default_branch": (default_branch or (existing or {}).get("default_branch") or "main"),
        "html_url": html_url or (existing or {}).get("html_url"),
        "private": private if private is not None else (existing or {}).get("private"),
        "repo_path": resolved_path,
        "connected_at": _now(),
    }
    if resolved_installation:
        doc["installation_id"] = str(resolved_installation)
    repos().replace_one({"_id": CONNECTED_ID}, doc, upsert=True)

    update: dict[str, Any] = {"repo": doc["full_name"]}
    if doc.get("repo_path"):
        update["repo_path"] = doc["repo_path"]

    if propagate_api_ids is not None:
        if propagate_api_ids:
            apis().update_many({"_id": {"$in": list(propagate_api_ids)}}, {"$set": update})
    elif propagate_to_apis:
        apis().update_many({}, {"$set": update})

    return doc


def disconnect_repo(*, clear_api_repos: bool = False) -> bool:
    """Remove the connected-repo binding. Returns True if something was deleted."""
    result = repos().delete_one({"_id": CONNECTED_ID})
    if clear_api_repos:
        apis().update_many({}, {"$set": {"repo": None}, "$unset": {"repo_path": ""}})
    return result.deleted_count > 0


def connected_summary(doc: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Public shape for API responses (no secrets)."""
    doc = doc if doc is not None else get_connected_repo()
    if not doc:
        return None
    return {
        "full_name": doc.get("full_name"),
        "owner": doc.get("owner"),
        "name": doc.get("name"),
        "default_branch": doc.get("default_branch"),
        "html_url": doc.get("html_url"),
        "private": doc.get("private"),
        "repo_path": doc.get("repo_path"),
        "connected_at": doc.get("connected_at"),
    }
