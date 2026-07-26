"""MongoDB access package — the only place that talks to Mongo directly."""

from db.client import apis, changes, get_client, get_db, set_client_override, spec_versions
from db.schemas import ensure_indexes

__all__ = [
    "apis",
    "changes",
    "ensure_indexes",
    "get_client",
    "get_db",
    "set_client_override",
    "spec_versions",
]
