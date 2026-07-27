"""Reset Mongo to a clean prod-style workspace (no demo APIs by default)."""

from __future__ import annotations

from db.client import apis, changes, get_db, repos, spec_versions
from db.schemas import ensure_indexes
from db.seed import DEMO_API_ID, LIVE_API_ID, seed


def reset(*, demo: bool = False) -> dict:
    """Wipe watched-API data. Re-seed demo fixtures only when ``demo=True``."""
    db = get_db()
    ensure_indexes(db)
    deleted = {
        "changes": changes().delete_many({}).deleted_count,
        "spec_versions": spec_versions().delete_many({}).deleted_count,
        "apis": apis().delete_many({}).deleted_count,
        "repos": repos().delete_many({}).deleted_count,
    }
    seeded = seed(force=True, demo=demo)
    _ = db
    return {"deleted": deleted, "seeded": seeded, "demo": demo}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Reset SelfPI MongoDB")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Also re-seed Stripe demo + live fixtures",
    )
    args = parser.parse_args()
    # Drop legacy demo ids even when not re-seeding demo
    _ = (DEMO_API_ID, LIVE_API_ID)
    result = reset(demo=args.demo)
    print(f"Reset: {result}")


if __name__ == "__main__":
    main()
