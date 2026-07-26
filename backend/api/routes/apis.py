"""Watched APIs routes — GET/POST /apis, GET /apis/{id}, POST /apis/{id}/check."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from api.models import ApiSummary, CheckApiResponse, CreateApiRequest
from db.client import apis
from scanner.ir.enums import ApiStatus

router = APIRouter(prefix="/apis", tags=["apis"])


def _doc_to_summary(doc: dict) -> ApiSummary:
    return ApiSummary(
        id=str(doc["_id"]),
        name=doc.get("name", ""),
        current_version=doc.get("current_version"),
        status=ApiStatus(doc.get("status", ApiStatus.UP_TO_DATE)),
        languages=doc.get("languages", []),
        last_checked=doc.get("last_checked"),
        open_change_count=doc.get("open_change_count", 0),
        repo=doc.get("repo"),
        spec_url=doc.get("spec_url"),
    )


@router.get("", response_model=list[ApiSummary])
def list_apis() -> list[ApiSummary]:
    return [_doc_to_summary(doc) for doc in apis().find()]


@router.post("", response_model=ApiSummary, status_code=201)
def create_api(body: CreateApiRequest) -> ApiSummary:
    if apis().find_one({"_id": body.id}):
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "api_exists", "message": f"API '{body.id}' already watched"}},
        )
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    doc = {
        "_id": body.id,
        "name": body.name,
        "spec_url": body.spec_url,
        "repo": body.repo,
        "languages": body.languages,
        "current_version": None,
        "status": ApiStatus.UP_TO_DATE.value,
        "last_checked": now,
        "open_change_count": 0,
    }
    apis().insert_one(doc)
    return _doc_to_summary(doc)


@router.get("/{api_id}", response_model=ApiSummary)
def get_api(api_id: str) -> ApiSummary:
    doc = apis().find_one({"_id": api_id})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"API '{api_id}' not found"}},
        )
    return _doc_to_summary(doc)


@router.post("/{api_id}/check", response_model=CheckApiResponse)
def check_api(api_id: str) -> CheckApiResponse:
    doc = apis().find_one({"_id": api_id})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"API '{api_id}' not found"}},
        )
    # Watcher poll wired in later milestones; stub acknowledges the trigger.
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    apis().update_one({"_id": api_id}, {"$set": {"last_checked": now}})
    return CheckApiResponse(checked=True, new_version=None, changes_detected=0)
