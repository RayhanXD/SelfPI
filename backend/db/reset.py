"""Reset Mongo collections to a clean demo seed (drops polluted changes/specs)."""

from __future__ import annotations

from db.client import apis, changes, get_db, spec_versions
from db.seed import DEMO_API_ID, LIVE_API_ID, seed


def reset() -> dict:
    """Delete watched-API data and re-seed demo + live APIs."""
    db = get_db()
    deleted = {
        "changes": changes().delete_many({}).deleted_count,
        "spec_versions": spec_versions().delete_many({}).deleted_count,
        "apis": apis().delete_many({"_id": {"$in": [DEMO_API_ID, LIVE_API_ID]}}).deleted_count,
    }
    # Also drop legacy single-id pollution if present under other names
    _ = db  # keep import used for connection warm-up
    seeded = seed(force=True)
    return {"deleted": deleted, "seeded": seeded}


def main() -> None:
    result = reset()
    print(f"Reset: {result}")


if __name__ == "__main__":
    main()
