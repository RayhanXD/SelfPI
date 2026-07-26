"""Ping MongoDB using MONGODB_URI from settings."""

from __future__ import annotations

from db.client import get_client
from db.settings import get_settings


def check_mongo() -> None:
    settings = get_settings()
    print(f"→ Checking MongoDB at {settings.mongodb_uri} …")
    client = get_client()
    client.admin.command("ping")
    print("→ MongoDB OK")


def main() -> None:
    check_mongo()


if __name__ == "__main__":
    main()
