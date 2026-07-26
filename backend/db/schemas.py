"""Collection schemas, indexes, and ensure_indexes() for M0."""

from __future__ import annotations

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

# Document shapes (see docs/self-maintaining-apis-design.md §8)

API_SCHEMA = {
    "_id": "stripe",
    "name": "Stripe",
    "spec_url": "https://example.com/openapi.json",
    "repo": "myorg/billing-app",
    "current_version": "2026-06-01",
    "status": "up_to_date",  # up_to_date | change_detected | breaking_change_unhandled
    "languages": ["python"],
    "last_checked": None,
    "open_change_count": 0,
}

SPEC_VERSION_SCHEMA = {
    "_id": "ObjectId",
    "api_id": "stripe",
    "version": "2026-06-01",
    "fetched_at": "ISO-8601",
    "spec": {"openapi": "3.1.0", "paths": {}},
}

CHANGE_SCHEMA = {
    "_id": "ObjectId",
    "api_id": "stripe",
    "operation_id": "createCharge",
    "kind": "renamed_param",  # removed_field | renamed_param | type_changed | value_deprecated
    "detail": {},
    "from_version": "2026-06-01",
    "to_version": "2026-07-01",
    "detected_at": "ISO-8601",
    "repo": "myorg/billing-app",
    "status": "detected",  # detected | scanning | pr_open | merged | dismissed
    "call_sites": [],  # embedded CallSite[]
    "pr": None,  # embedded { number, url, state, tests_passing, opened_at }
}


def ensure_indexes(db: Database) -> None:
    """Create indexes matching design doc access patterns."""
    db["spec_versions"].create_index(
        [("api_id", ASCENDING), ("version", DESCENDING)],
        name="api_id_version",
    )
    db["changes"].create_index(
        [("api_id", ASCENDING), ("detected_at", DESCENDING)],
        name="api_id_detected_at",
    )
    db["changes"].create_index(
        [("status", ASCENDING), ("detected_at", DESCENDING)],
        name="status_detected_at",
    )
    db["apis"].create_index([("status", ASCENDING)], name="status")
