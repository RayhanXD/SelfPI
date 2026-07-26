"""Spec version routes — list stored versions + demo bump endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from api.models import PushSpecRequest, PushSpecResponse, SpecVersionSummary
from db.client import apis, spec_versions

router = APIRouter(prefix="/apis", tags=["specs"])


@router.get("/{api_id}/spec-versions", response_model=list[SpecVersionSummary])
def list_spec_versions(api_id: str) -> list[SpecVersionSummary]:
    if not apis().find_one({"_id": api_id}):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"API '{api_id}' not found"}},
        )
    docs = spec_versions().find({"api_id": api_id}).sort("version", -1)
    return [
        SpecVersionSummary(version=d["version"], fetched_at=d.get("fetched_at")) for d in docs
    ]


@router.post("/{api_id}/spec-versions", response_model=PushSpecResponse)
def push_spec_version(api_id: str, body: PushSpecRequest) -> PushSpecResponse:
    """Test/demo only — the 'bump' button that triggers the loop on demand."""
    if not apis().find_one({"_id": api_id}):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"API '{api_id}' not found"}},
        )
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    spec_versions().insert_one(
        {
            "api_id": api_id,
            "version": body.version,
            "fetched_at": now,
            "spec": body.spec,
        }
    )
    apis().update_one(
        {"_id": api_id},
        {
            "$set": {
                "current_version": body.version,
                "last_checked": now,
                "status": "change_detected",
            }
        },
    )
    # Diff + scan wired in M1–M4; bump stores the version for now.
    return PushSpecResponse(version=body.version, changes_detected=0)
