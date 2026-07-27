"""Seed demo + live watched APIs for local/dev bootstrap."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from db.client import apis, get_db, spec_versions
from db.schemas import ensure_indexes

SAMPLE_REPO = str((Path(__file__).resolve().parents[2] / "fixtures" / "sample_repo").resolve())

DEMO_API_ID = "stripe-demo"
DEMO_VERSION = "2026-06-01"
LIVE_API_ID = "stripe"

DEMO_SPEC = {
    "openapi": "3.1.0",
    "info": {"title": "Stripe (demo)", "version": DEMO_VERSION},
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

# Back-compat aliases used by older scripts/tests
SEED_API_ID = DEMO_API_ID
SEED_VERSION = DEMO_VERSION
SEED_SPEC = DEMO_SPEC


def seed(*, force: bool = False) -> dict:
    """Insert seed documents if missing. Returns counts of what was written."""
    db = get_db()
    ensure_indexes(db)

    written = {"apis": 0, "spec_versions": 0}
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # --- Demo API (Bump spec only) -----------------------------------------
    existing_demo = apis().find_one({"_id": DEMO_API_ID})
    if existing_demo is None or force:
        apis().replace_one(
            {"_id": DEMO_API_ID},
            {
                "_id": DEMO_API_ID,
                "name": "Stripe (demo)",
                "mode": "demo",
                "spec_url": None,
                "repo": "RayhanXD/WishBot",
                "repo_path": SAMPLE_REPO,
                "current_version": DEMO_VERSION,
                "status": "up_to_date",
                "languages": ["python"],
                "last_checked": now,
                "open_change_count": 0,
            },
            upsert=True,
        )
        written["apis"] += 1

    existing_demo_spec = spec_versions().find_one(
        {"api_id": DEMO_API_ID, "version": DEMO_VERSION}
    )
    if existing_demo_spec is None or force:
        if existing_demo_spec and force:
            spec_versions().delete_many({"api_id": DEMO_API_ID, "version": DEMO_VERSION})
        spec_versions().insert_one(
            {
                "api_id": DEMO_API_ID,
                "version": DEMO_VERSION,
                "fetched_at": now,
                "spec": DEMO_SPEC,
            }
        )
        written["spec_versions"] += 1

    # --- Live Stripe (Check now only) — no seed spec; first poll stores baseline
    existing_live = apis().find_one({"_id": LIVE_API_ID})
    if existing_live is None or force:
        apis().replace_one(
            {"_id": LIVE_API_ID},
            {
                "_id": LIVE_API_ID,
                "name": "Stripe",
                "mode": "live",
                "spec_url": (
                    "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"
                ),
                "repo": "RayhanXD/WishBot",
                "repo_path": SAMPLE_REPO,
                "current_version": None,
                "status": "up_to_date",
                "languages": ["python"],
                "last_checked": None,
                "open_change_count": 0,
            },
            upsert=True,
        )
        written["apis"] += 1

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
