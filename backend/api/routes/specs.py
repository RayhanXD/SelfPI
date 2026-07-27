"""Spec version routes — list stored versions + demo bump endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from api.models import PushSpecRequest, PushSpecResponse, SpecVersionSummary
from db.bson_safe import bson_safe
from db.client import apis, spec_versions
from pipeline.process import process_spec_bump
from watcher import fingerprint as spec_fingerprint

router = APIRouter(prefix="/apis", tags=["specs"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/{api_id}/spec-versions", response_model=list[SpecVersionSummary])
def list_spec_versions(api_id: str) -> list[SpecVersionSummary]:
    if not apis().find_one({"_id": api_id}):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"API '{api_id}' not found"}},
        )
    docs = spec_versions().find({"api_id": api_id}).sort("fetched_at", -1)
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

    safe_spec = bson_safe(body.spec)
    spec_versions().insert_one(
        {
            "api_id": api_id,
            "version": body.version,
            "fetched_at": _now(),
            "spec": safe_spec,
            "fingerprint": spec_fingerprint(safe_spec),
        }
    )
    from db.settings import pr_pipeline_flags

    open_pr, dry_run_pr = pr_pipeline_flags()
    result = process_spec_bump(
        api_id,
        version=body.version,
        spec=safe_spec,
        open_pr=open_pr,
        dry_run_pr=dry_run_pr,
    )
    return PushSpecResponse(
        version=body.version,
        changes_detected=result["changes_detected"],
    )
