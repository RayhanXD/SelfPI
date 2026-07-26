"""Seed one apis doc + one spec_versions doc for local/dev bootstrap."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from db.client import apis, get_db, spec_versions
from db.schemas import ensure_indexes

SEED_API_ID = "stripe"
SEED_VERSION = "2026-06-01"
SAMPLE_REPO = str((Path(__file__).resolve().parents[2] / "fixtures" / "sample_repo"))


SEED_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Stripe (seed)", "version": SEED_VERSION},
    "paths": {
        "/v1/charges": {
            "post": {
                "operationId": "createCharge",
                "summary": "Create a charge",
                "parameters": [
                    {
                        "name": "source",
                        "in": "query",
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            }
        }
    },
}


def seed(*, force: bool = False) -> dict:
    """Insert seed documents if missing. Returns counts of what was written."""
    db = get_db()
    ensure_indexes(db)

    written = {"apis": 0, "spec_versions": 0}
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    existing_api = apis().find_one({"_id": SEED_API_ID})
    if existing_api is None or force:
        apis().replace_one(
            {"_id": SEED_API_ID},
            {
                "_id": SEED_API_ID,
                "name": "Stripe",
                "spec_url": "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json",
                "repo": "myorg/billing-app",
                "repo_path": SAMPLE_REPO,
                "current_version": SEED_VERSION,
                "status": "up_to_date",
                "languages": ["python"],
                "last_checked": now,
                "open_change_count": 0,
            },
            upsert=True,
        )
        written["apis"] = 1

    existing_spec = spec_versions().find_one({"api_id": SEED_API_ID, "version": SEED_VERSION})
    if existing_spec is None or force:
        if existing_spec and force:
            spec_versions().delete_many({"api_id": SEED_API_ID, "version": SEED_VERSION})
        spec_versions().insert_one(
            {
                "api_id": SEED_API_ID,
                "version": SEED_VERSION,
                "fetched_at": now,
                "spec": SEED_SPEC,
            }
        )
        written["spec_versions"] = 1

    return written


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed SelfPI MongoDB collections")
    parser.add_argument("--force", action="store_true", help="Overwrite existing seed docs")
    args = parser.parse_args()
    result = seed(force=args.force)
    print(f"Seeded: {result}")


if __name__ == "__main__":
    main()
