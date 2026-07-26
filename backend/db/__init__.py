"""MongoDB access package — the only place that talks to Mongo directly."""

from db.client import apis, changes, get_client, get_db, spec_versions
from db.schemas import ensure_indexes
from db.seed import seed

__all__ = [
    "apis",
    "changes",
    "ensure_indexes",
    "get_client",
    "get_db",
    "seed",
    "spec_versions",
]
