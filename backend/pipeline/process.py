"""End-to-end pipeline: new spec → diff → scan → adjudicate → (optional) PR → Mongo."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bson import ObjectId

from db.client import apis, changes, spec_versions
from db.settings import get_settings
from diff.engine import detect_breaking_changes
from diff.types import BreakingChange
from llm.client import get_llm_client
from patcher import generate_and_open_pr
from pipeline.spec_diff import build_spec_diff
from scanner import scan
from scanner.adjudicator import adjudicate
from scanner.ir.enums import ApiStatus, ChangeStatus


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_repo_path(api_doc: dict[str, Any] | None = None) -> Path:
    """Local checkout to scan. Prefer per-api repo_path, then settings, then fixtures."""
    if api_doc and api_doc.get("repo_path"):
        return Path(api_doc["repo_path"]).expanduser().resolve()
    settings = get_settings()
    if settings.repo_path:
        return Path(settings.repo_path).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "fixtures" / "sample_repo").resolve()


def process_spec_bump(
    api_id: str,
    *,
    version: str,
    spec: dict[str, Any],
    from_version: str | None = None,
    open_pr: bool = False,
    dry_run_pr: bool = True,
) -> dict[str, Any]:
    """Diff the new spec against the previous stored version and process each change.

    Assumes the new `spec_versions` doc for `version` is already stored.
    """
    api_doc = apis().find_one({"_id": api_id})
    if not api_doc:
        raise KeyError(f"API '{api_id}' not found")

    prev = _previous_spec(api_id, version, from_version=from_version)
    if prev is None:
        apis().update_one(
            {"_id": api_id},
            {
                "$set": {
                    "current_version": version,
                    "last_checked": _now(),
                    "status": ApiStatus.UP_TO_DATE.value,
                }
            },
        )
        return {"changes_detected": 0, "change_ids": []}

    breaking = detect_breaking_changes(prev["spec"], spec)
    change_ids: list[str] = []

    repo_path = resolve_repo_path(api_doc)
    language = (api_doc.get("languages") or ["python"])[0]
    repo_name = api_doc.get("repo") or "local/repo"

    for bc in breaking:
        doc_id = process_breaking_change(
            api_id=api_id,
            change=bc,
            from_version=prev["version"],
            to_version=version,
            repo=repo_name,
            repo_path=repo_path,
            language=language,
            open_pr=open_pr,
            dry_run_pr=dry_run_pr,
        )
        change_ids.append(doc_id)

    _refresh_api_status(api_id, current_version=version)
    return {"changes_detected": len(change_ids), "change_ids": change_ids}


def process_breaking_change(
    *,
    api_id: str,
    change: BreakingChange,
    from_version: str,
    to_version: str,
    repo: str,
    repo_path: Path,
    language: str = "python",
    open_pr: bool = False,
    dry_run_pr: bool = True,
) -> str:
    """Scan + adjudicate one BreakingChange; persist embedded call sites (+ optional PR)."""
    now = _now()
    doc = {
        "api_id": api_id,
        "operation_id": change.operation_id,
        "kind": change.kind.value,
        "detail": change.detail,
        "from_version": from_version,
        "to_version": to_version,
        "detected_at": now,
        "repo": repo,
        "status": ChangeStatus.SCANNING.value,
        "spec_diff": build_spec_diff(change),
        "call_sites": [],
        "pr": None,
    }
    change_id = changes().insert_one(doc).inserted_id

    call_sites = []
    if repo_path.is_dir():
        call_sites = scan(str(repo_path), change, language=language)
        call_sites = adjudicate(
            call_sites,
            change_context=change.model_dump(mode="json"),
            llm=get_llm_client(),
        )

    status = ChangeStatus.DETECTED
    pr_embed = None
    if open_pr and call_sites:
        pr_result = generate_and_open_pr(
            call_sites,
            change,
            repo=repo,
            repo_path=repo_path,
            dry_run=dry_run_pr,
            llm=get_llm_client(),
        )
        # Only persist a PR embed when a real (or intentional) PR was opened —
        # dry-run must not pretend a GitHub PR exists in the UI.
        if not pr_result.get("dry_run"):
            pr_embed = {
                "number": pr_result.get("number", 0),
                "url": pr_result.get("url"),
                "state": pr_result.get("state", "open"),
                "tests_passing": pr_result.get("tests_passing"),
                "opened_at": pr_result.get("opened_at") or now,
            }
            status = ChangeStatus.PR_OPEN

    changes().update_one(
        {"_id": change_id},
        {
            "$set": {
                "status": status.value,
                "call_sites": [s.to_mongo() for s in call_sites],
                "pr": pr_embed,
            }
        },
    )
    return str(change_id)


def open_change_pr(
    change_id: str,
    *,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """Open (or dry-run) a fix PR for an existing change with call sites."""
    oid = ObjectId(change_id)
    doc = changes().find_one({"_id": oid})
    if not doc:
        raise KeyError(f"Change '{change_id}' not found")

    raw_sites = doc.get("call_sites") or []
    if not raw_sites:
        raise ValueError("Change has no call sites to patch")

    from scanner.ir.types import CallSite

    call_sites = [CallSite.model_validate(cs) for cs in raw_sites]
    change = BreakingChange(
        operation_id=doc["operation_id"],
        kind=doc["kind"],
        detail=doc.get("detail") or {},
    )
    api_doc = apis().find_one({"_id": doc["api_id"]}) or {}
    repo_path = resolve_repo_path(api_doc)
    repo_name = doc.get("repo") or api_doc.get("repo") or "local/repo"

    if dry_run is None:
        from db.settings import github_ready

        dry_run = not github_ready()

    now = _now()
    pr_result = generate_and_open_pr(
        call_sites,
        change,
        repo=repo_name,
        repo_path=repo_path,
        dry_run=dry_run,
        llm=get_llm_client(),
    )

    if pr_result.get("dry_run"):
        return {
            "change_id": change_id,
            "status": doc.get("status", ChangeStatus.DETECTED.value),
            "pr": None,
            "dry_run": True,
            "edited_files": pr_result.get("edited_files") or [],
            "note": pr_result.get("note")
            or "Dry-run only — configure GitHub App to open a real PR",
        }

    pr_embed = {
        "number": pr_result.get("number", 0),
        "url": pr_result.get("url"),
        "state": pr_result.get("state", "open"),
        "tests_passing": pr_result.get("tests_passing"),
        "opened_at": pr_result.get("opened_at") or now,
    }
    changes().update_one(
        {"_id": oid},
        {"$set": {"status": ChangeStatus.PR_OPEN.value, "pr": pr_embed}},
    )
    _refresh_api_status(doc["api_id"])
    return {
        "change_id": change_id,
        "status": ChangeStatus.PR_OPEN.value,
        "pr": pr_embed,
        "dry_run": False,
        "edited_files": pr_result.get("edited_files") or [],
    }


def rescan_change(change_id: str) -> dict[str, Any]:
    """Re-run scanner + adjudicator for an existing change document."""
    oid = ObjectId(change_id)
    doc = changes().find_one({"_id": oid})
    if not doc:
        raise KeyError(f"Change '{change_id}' not found")

    api_doc = apis().find_one({"_id": doc["api_id"]}) or {}
    repo_path = resolve_repo_path(api_doc)
    language = (api_doc.get("languages") or ["python"])[0]
    change = BreakingChange(
        operation_id=doc["operation_id"],
        kind=doc["kind"],
        detail=doc.get("detail") or {},
    )

    changes().update_one({"_id": oid}, {"$set": {"status": ChangeStatus.SCANNING.value}})
    call_sites = []
    if repo_path.is_dir():
        call_sites = scan(str(repo_path), change, language=language)
        call_sites = adjudicate(
            call_sites,
            change_context=change.model_dump(mode="json"),
            llm=get_llm_client(),
        )

    changes().update_one(
        {"_id": oid},
        {
            "$set": {
                "status": ChangeStatus.DETECTED.value,
                "call_sites": [s.to_mongo() for s in call_sites],
            }
        },
    )
    _refresh_api_status(doc["api_id"])
    return {"call_site_count": len(call_sites), "status": ChangeStatus.DETECTED.value}


def _refresh_api_status(api_id: str, *, current_version: str | None = None) -> None:
    open_statuses = [
        ChangeStatus.DETECTED.value,
        ChangeStatus.SCANNING.value,
        ChangeStatus.PR_OPEN.value,
    ]
    open_count = changes().count_documents({"api_id": api_id, "status": {"$in": open_statuses}})
    unhandled = changes().count_documents(
        {
            "api_id": api_id,
            "status": {"$in": [ChangeStatus.DETECTED.value, ChangeStatus.SCANNING.value]},
        }
    )
    if unhandled:
        status = ApiStatus.BREAKING_CHANGE_UNHANDLED.value
    elif open_count:
        status = ApiStatus.CHANGE_DETECTED.value
    else:
        status = ApiStatus.UP_TO_DATE.value

    fields: dict[str, Any] = {
        "last_checked": _now(),
        "status": status,
        "open_change_count": open_count,
    }
    if current_version is not None:
        fields["current_version"] = current_version
    apis().update_one({"_id": api_id}, {"$set": fields})


def _previous_spec(
    api_id: str, new_version: str, *, from_version: str | None = None
) -> dict[str, Any] | None:
    if from_version:
        return spec_versions().find_one({"api_id": api_id, "version": from_version})
    docs = list(
        spec_versions()
        .find({"api_id": api_id, "version": {"$ne": new_version}})
        .sort("fetched_at", -1)
        .limit(1)
    )
    return docs[0] if docs else None
