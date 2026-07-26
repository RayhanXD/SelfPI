"""MongoDB client + collection accessors. All Mongo access goes through this package."""

from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from db.settings import get_settings

COLLECTIONS = ("apis", "spec_versions", "changes")


@lru_cache
def get_client() -> MongoClient:
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
