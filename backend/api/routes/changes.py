"""Changes routes — feed, detail, dismiss, rescan, open-pr."""

from __future__ import annotations

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pymongo import ReturnDocument

from api.models import (
    ChangeDetail,
    ChangeListResponse,
    ChangeSummary,
    PrSummary,
    RescanResponse,
    SpecDiff,
)
from db.client import changes
from scanner.ir.enums import ChangeKind, ChangeStatus, PrState
from scanner.ir.types import CallSite

router = APIRouter(prefix="/changes", tags=["changes"])


def _pr_from_doc(pr: dict | None) -> PrSummary | None:
    if not pr:
        return None
    return PrSummary(
        number=pr["number"],
        url=pr.get("url"),
        state=PrState(pr.get("state", PrState.OPEN)),
        tests_passing=pr.get("tests_passing"),
        opened_at=pr.get("opened_at"),
    )


def _summary_from_doc(doc: dict) -> ChangeSummary:
    call_sites = doc.get("call_sites") or []
    return ChangeSummary(
        id=str(doc["_id"]),
        api_id=doc["api_id"],
        operation_id=doc["operation_id"],
        kind=ChangeKind(doc["kind"]),
        detail=doc.get("detail") or {},
        call_site_count=len(call_sites),
        status=ChangeStatus(doc.get("status", ChangeStatus.DETECTED)),
        pr=_pr_from_doc(doc.get("pr")),
        detected_at=doc.get("detected_at"),
    )


def _detail_from_doc(doc: dict) -> ChangeDetail:
    raw_sites = doc.get("call_sites") or []
    call_sites = [CallSite.model_validate(cs) for cs in raw_sites]
    spec_diff = None
    if doc.get("spec_diff"):
        spec_diff = SpecDiff.model_validate(doc["spec_diff"])
    return ChangeDetail(
        id=str(doc["_id"]),
        api_id=doc["api_id"],
        operation_id=doc["operation_id"],
        kind=ChangeKind(doc["kind"]),
        detail=doc.get("detail") or {},
        from_version=doc.get("from_version"),
        to_version=doc.get("to_version"),
        status=ChangeStatus(doc.get("status", ChangeStatus.DETECTED)),
        repo=doc.get("repo"),
        spec_diff=spec_diff,
        call_sites=call_sites,
        pr=_pr_from_doc(doc.get("pr")),
        detected_at=doc.get("detected_at"),
    )


@router.get("", response_model=ChangeListResponse)
def list_changes(
    api_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = None,
) -> ChangeListResponse:
    query: dict = {}
    if api_id:
        query["api_id"] = api_id
    if status:
        query["status"] = status
    if cursor:
        query["_id"] = {"$lt": ObjectId(cursor)}

    docs = list(changes().find(query).sort("detected_at", -1).limit(limit + 1))
    next_cursor = None
    if len(docs) > limit:
        docs = docs[:limit]
        next_cursor = str(docs[-1]["_id"])
    return ChangeListResponse(items=[_summary_from_doc(d) for d in docs], next_cursor=next_cursor)


@router.get("/{change_id}", response_model=ChangeDetail)
def get_change(change_id: str) -> ChangeDetail:
    try:
        oid = ObjectId(change_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "invalid_id", "message": "Invalid change id"}},
        ) from exc
    doc = changes().find_one({"_id": oid})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"Change '{change_id}' not found"}},
        )
    return _detail_from_doc(doc)


@router.post("/{change_id}/dismiss", response_model=ChangeSummary)
def dismiss_change(change_id: str) -> ChangeSummary:
    try:
        oid = ObjectId(change_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "invalid_id", "message": "Invalid change id"}},
        ) from exc
    result = changes().find_one_and_update(
        {"_id": oid},
        {"$set": {"status": ChangeStatus.DISMISSED.value}},
        return_document=ReturnDocument.AFTER,
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"Change '{change_id}' not found"}},
        )
    from pipeline.process import _refresh_api_status

    _refresh_api_status(result["api_id"])
    return _summary_from_doc(result)


@router.post("/{change_id}/rescan", response_model=RescanResponse)
def rescan_change_route(change_id: str) -> RescanResponse:
    try:
        ObjectId(change_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "invalid_id", "message": "Invalid change id"}},
        ) from exc
    try:
        from pipeline.process import rescan_change

        result = rescan_change(change_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": str(exc)}},
        ) from exc
    return RescanResponse(
        call_site_count=result["call_site_count"],
        status=ChangeStatus(result["status"]),
    )


@router.post("/{change_id}/open-pr", response_model=ChangeSummary)
def open_pr_route(change_id: str) -> ChangeSummary:
    """Open a fix PR for this change (requires GitHub App; otherwise 503)."""
    try:
        ObjectId(change_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "invalid_id", "message": "Invalid change id"}},
        ) from exc

    from db.settings import github_ready
    from pipeline.process import open_change_pr

    if not github_ready():
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "github_not_configured",
                    "message": (
                        "GitHub App not configured. Set GITHUB_APP_ID, "
                        "GITHUB_APP_PRIVATE_KEY, and GITHUB_APP_INSTALLATION_ID."
                    ),
                }
            },
        )

    try:
        result = open_change_pr(change_id, dry_run=False)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": str(exc)}},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "no_call_sites", "message": str(exc)}},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": {"code": "pr_failed", "message": str(exc)}},
        ) from exc

    if result.get("dry_run"):
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "github_not_configured",
                    "message": result.get("note") or "GitHub App not configured",
                }
            },
        )

    doc = changes().find_one({"_id": ObjectId(change_id)})
    assert doc is not None
    return _summary_from_doc(doc)
