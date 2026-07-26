"""MongoDB client + collection accessors. All Mongo access goes through this package."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from db.settings import get_settings

COLLECTIONS = ("apis", "spec_versions", "changes")

_client_override: Any | None = None


def set_client_override(client: Any | None) -> None:
    """Test helper — inject mongomock (or similar). Pass None to clear."""
    global _client_override
    _client_override = client
    get_client.cache_clear()


@lru_cache
def get_client() -> MongoClient:
    if _client_override is not None:
        return _client_override
    settings = get_settings()
    return MongoClient(settings.mongodb_uri)


def get_db() -> Database:
    settings = get_settings()
    return get_client()[settings.mongodb_db]


def apis() -> Collection:
    return get_db()["apis"]


def spec_versions() -> Collection:
    return get_db()["spec_versions"]


def changes() -> Collection:
    return get_db()["changes"]
