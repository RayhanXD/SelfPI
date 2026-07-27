"""Seed demo + live watched APIs for local/dev bootstrap."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from db.client import apis, get_db, spec_versions
from db.repos import connect_repo, get_connected_repo
from db.schemas import ensure_indexes

SAMPLE_REPO = str((Path(__file__).resolve().parents[2] / "fixtures" / "sample_repo").resolve())
DEMO_CONSUMER = str((Path(__file__).resolve().parents[2] / "demo-consumer").resolve())
DEMO_GITHUB_REPO = "RayhanXD/selfpi-demo-consumer"

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


def _scan_repo_path() -> str:
    """Prefer local demo-consumer when present; else fixtures/sample_repo."""
    path = Path(DEMO_CONSUMER)
    return str(path) if path.is_dir() else SAMPLE_REPO


def seed(*, force: bool = False) -> dict:
    """Insert seed documents if missing. Returns counts of what was written."""
    db = get_db()
    ensure_indexes(db)

    written = {"apis": 0, "spec_versions": 0, "repos": 0}
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    scan_path = _scan_repo_path()

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
                "repo": DEMO_GITHUB_REPO,
                "repo_path": scan_path,
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

    # --- Live Stripe (Check now only) — never seed a demo/tiny spec onto live.
    # First successful poll stores a quiet baseline (changes_detected: 0).
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
                "repo": DEMO_GITHUB_REPO,
                "repo_path": scan_path,
                "current_version": None,
                "status": "up_to_date",
                "languages": ["python"],
                "last_checked": None,
                "open_change_count": 0,
            },
            upsert=True,
        )
        written["apis"] += 1
        # Force re-seed clears poisoned live priors (demo tiny under live id).
        if force:
            spec_versions().delete_many({"api_id": LIVE_API_ID})
    else:
        # Soft cleanup: drop demo seed if it was wrongly keyed as live Stripe.
        for doc in list(spec_versions().find({"api_id": LIVE_API_ID})):
            spec = doc.get("spec") or {}
            info = spec.get("info") or {}
            paths = spec.get("paths") or {}
            is_demo_orphan = info.get("title") == "Stripe (demo)" or (
                list(paths.keys()) == ["/v1/charges"] and len(paths) == 1
            )
            if not is_demo_orphan:
                continue
            spec_versions().delete_one({"_id": doc["_id"]})
            if existing_live.get("current_version") == doc.get("version"):
                apis().update_one(
                    {"_id": LIVE_API_ID},
                    {"$set": {"current_version": None}},
                )

    # --- Connected repo binding (Settings → Connect repo) ------------------
    if get_connected_repo() is None or force:
        connect_repo(
            full_name=DEMO_GITHUB_REPO,
            owner=DEMO_GITHUB_REPO.split("/", 1)[0],
            name=DEMO_GITHUB_REPO.split("/", 1)[1],
            default_branch="main",
            html_url=f"https://github.com/{DEMO_GITHUB_REPO}",
            private=False,
            repo_path=scan_path,
            propagate_to_apis=False,  # seed already set repo on APIs
        )
        written["repos"] = 1

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
