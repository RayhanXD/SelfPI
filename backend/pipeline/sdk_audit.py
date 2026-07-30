"""Consumer SDK drift audit — catch legacy pins the OpenAPI poll will never see.

Example: WishBot pins openai==0.28.1 and calls openai.Audio.transcribe.
Polling today's OpenAI OpenAPI fingerprint stays unchanged forever; this audit
surfaces that as an actionable breaking change against the connected repo.
"""

from __future__ import annotations

import logging
from typing import Any

from db.client import apis, changes
from detector.consumer_versions import (
    consumer_package_versions,
    parse_version,
    version_less,
)
from detector.catalog import get_entry
from diff.types import BreakingChange
from pipeline.process import process_breaking_change, resolve_repo_path
from scanner.ir.enums import ChangeKind, ChangeStatus

logger = logging.getLogger("selfpi.sdk_audit")

# Known legacy SDK ceilings — pin strictly below this is treated as drift.
_LEGACY_CEILING: dict[str, tuple[int, ...]] = {
    "openai": (1, 0, 0),
}

# Synthetic breaks emitted for a legacy openai 0.x pin (surface → modern op).
_OPENAI_LEGACY_BREAKS: tuple[BreakingChange, ...] = (
    BreakingChange(
        operation_id="createTranscription",
        kind=ChangeKind.REMOVED_FIELD,
        detail={
            "reason": "legacy_sdk",
            "package": "openai",
            "surface": "openai.Audio.transcribe",
            "replacement": "client.audio.transcriptions.create",
            "note": "openai SDK 0.x Audio.transcribe was removed in v1+",
        },
    ),
    BreakingChange(
        operation_id="createChatCompletion",
        kind=ChangeKind.REMOVED_FIELD,
        detail={
            "reason": "legacy_sdk",
            "package": "openai",
            "surface": "openai.ChatCompletion.create",
            "replacement": "client.chat.completions.create",
            "note": "openai SDK 0.x ChatCompletion.create was removed in v1+",
        },
    ),
)


def audit_consumer_sdk(
    api_id: str,
    *,
    open_pr: bool = False,
    dry_run_pr: bool = True,
) -> dict[str, Any]:
    """If the connected checkout pins a known-legacy SDK, open change docs.

    Returns { audited, changes_detected, change_ids, pinned_version }.
    """
    api_doc = apis().find_one({"_id": api_id})
    if not api_doc:
        return {
            "audited": False,
            "changes_detected": 0,
            "change_ids": [],
            "pinned_version": None,
        }

    entry = get_entry(api_id)
    if entry is None:
        return {
            "audited": False,
            "changes_detected": 0,
            "change_ids": [],
            "pinned_version": None,
        }

    repo_path = resolve_repo_path(api_doc)
    if not repo_path.is_dir():
        return {
            "audited": False,
            "changes_detected": 0,
            "change_ids": [],
            "pinned_version": None,
        }

    versions = consumer_package_versions(repo_path)
    # Prefer catalog package names; fall back to api id.
    candidates = [_norm(p) for p in entry.python_packages] + [
        _norm(p) for p in entry.npm_packages
    ]
    if api_id not in candidates:
        candidates.append(_norm(api_id))

    pinned_raw: str | None = None
    pinned_tuple: tuple[int, ...] | None = None
    ceiling: tuple[int, ...] | None = None
    for name in candidates:
        if name in versions and name in _LEGACY_CEILING:
            pinned_raw = versions[name]
            pinned_tuple = parse_version(pinned_raw)
            ceiling = _LEGACY_CEILING[name]
            break

    if not pinned_raw or pinned_tuple is None or ceiling is None:
        return {
            "audited": True,
            "changes_detected": 0,
            "change_ids": [],
            "pinned_version": pinned_raw,
        }

    if not version_less(pinned_tuple, ceiling):
        return {
            "audited": True,
            "changes_detected": 0,
            "change_ids": [],
            "pinned_version": pinned_raw,
        }

    apis().update_one(
        {"_id": api_id},
        {
            "$set": {
                "consumer_package_version": pinned_raw,
                "consumer_sdk_legacy": True,
            }
        },
    )

    breaks = _breaks_for(api_id)
    if not breaks:
        return {
            "audited": True,
            "changes_detected": 0,
            "change_ids": [],
            "pinned_version": pinned_raw,
        }

    language = (api_doc.get("languages") or ["python"])[0]
    repo_name = api_doc.get("repo") or "local/repo"
    from_version = f"sdk-{pinned_raw}"
    to_version = api_doc.get("current_version") or "current"

    change_ids: list[str] = []
    for bc in breaks:
        detail = {**(bc.detail or {}), "pinned_version": pinned_raw}
        enriched = BreakingChange(
            operation_id=bc.operation_id,
            kind=bc.kind,
            detail=detail,
        )
        if _open_legacy_change_exists(api_id, enriched.operation_id):
            continue
        doc_id = process_breaking_change(
            api_id=api_id,
            change=enriched,
            from_version=from_version,
            to_version=str(to_version),
            repo=repo_name,
            repo_path=repo_path,
            language=language,
            open_pr=open_pr,
            dry_run_pr=dry_run_pr,
        )
        change_ids.append(doc_id)

    if change_ids:
        logger.info(
            "sdk audit %s: legacy pin %s → %d change(s)",
            api_id,
            pinned_raw,
            len(change_ids),
        )
        from pipeline.process import _refresh_api_status

        _refresh_api_status(api_id)

    return {
        "audited": True,
        "changes_detected": len(change_ids),
        "change_ids": change_ids,
        "pinned_version": pinned_raw,
    }


def _norm(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def _breaks_for(api_id: str) -> tuple[BreakingChange, ...]:
    if api_id == "openai":
        return _OPENAI_LEGACY_BREAKS
    return ()


def _open_legacy_change_exists(api_id: str, operation_id: str) -> bool:
    open_statuses = [
        ChangeStatus.DETECTED.value,
        ChangeStatus.SCANNING.value,
        ChangeStatus.PR_OPEN.value,
    ]
    return (
        changes().find_one(
            {
                "api_id": api_id,
                "operation_id": operation_id,
                "status": {"$in": open_statuses},
                "detail.reason": "legacy_sdk",
            }
        )
        is not None
    )
