"""Spec watcher — polls upstream OpenAPI specs and stores new versions.

Out: new spec_versions doc when the spec changes; then runs the pipeline.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import httpx

from db.client import apis, spec_versions
from pipeline.process import process_spec_bump


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def poll_api(api_id: str, *, open_pr: bool = False, dry_run_pr: bool = True) -> dict[str, Any]:
    """Fetch the current spec for an API; store a new version if it changed.

    Returns: { checked: bool, new_version: str | None, changes_detected: int }
    """
    api_doc = apis().find_one({"_id": api_id})
    if not api_doc:
        raise KeyError(f"API '{api_id}' not found")

    spec_url = api_doc.get("spec_url")
    if not spec_url:
        apis().update_one({"_id": api_id}, {"$set": {"last_checked": _now()}})
        return {"checked": True, "new_version": None, "changes_detected": 0}

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        resp = client.get(spec_url)
        resp.raise_for_status()
        spec = resp.json()

    version = _version_for(spec, api_doc)
    fingerprint = fingerprint_spec(spec)

    latest = list(
        spec_versions().find({"api_id": api_id}).sort("fetched_at", -1).limit(1)
    )
    if latest and latest[0].get("fingerprint") == fingerprint:
        apis().update_one({"_id": api_id}, {"$set": {"last_checked": _now()}})
        return {"checked": True, "new_version": None, "changes_detected": 0}

    # Avoid duplicate version ids — suffix with short hash when colliding
    if spec_versions().find_one({"api_id": api_id, "version": version}):
        version = f"{version}+{fingerprint[:8]}"

    spec_versions().insert_one(
        {
            "api_id": api_id,
            "version": version,
            "fetched_at": _now(),
            "spec": spec,
            "fingerprint": fingerprint,
        }
    )
    result = process_spec_bump(
        api_id,
        version=version,
        spec=spec,
        open_pr=open_pr,
        dry_run_pr=dry_run_pr,
    )
    return {
        "checked": True,
        "new_version": version,
        "changes_detected": result["changes_detected"],
    }


async def poll_api_async(api_id: str, **kwargs: Any) -> dict[str, Any]:
    """Async wrapper kept for the original watcher contract."""
    return poll_api(api_id, **kwargs)


def _version_for(spec: dict[str, Any], api_doc: dict[str, Any]) -> str:
    info = spec.get("info") or {}
    if info.get("version"):
        return str(info["version"])
    current = api_doc.get("current_version") or "0"
    return f"{current}-fetched-{_now()[:10]}"


def fingerprint(spec: dict[str, Any]) -> str:
    payload = json.dumps(spec, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


# Back-compat alias used during M4 wiring
fingerprint_spec = fingerprint
_fingerprint = fingerprint
