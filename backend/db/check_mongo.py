"""Fail fast if MongoDB is unreachable — used by `make check-mongo`."""

from __future__ import annotations

import sys

from pymongo.errors import PyMongoError

from db.client import create_mongo_client
from db.settings import get_settings


def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    uri = settings.mongodb_uri
    print(f"→ Checking MongoDB at { _redact(uri) } …", flush=True)
    try:
        client = create_mongo_client(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        client.close()
    except PyMongoError as exc:
        print("", file=sys.stderr)
        print("MongoDB is not reachable.", file=sys.stderr)
        print(f"  {exc}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Fix one of:", file=sys.stderr)
        print("  1) Atlas Network Access (TLS handshake errors usually mean IP blocked):", file=sys.stderr)
        print("     - Atlas → Network Access → Add IP Address → Allow Access from Anywhere", file=sys.stderr)
        print("       (0.0.0.0/0) for local dev, or add your current public IP", file=sys.stderr)
        print("     - Put the mongodb+srv:// URI in backend/.env as MONGODB_URI", file=sys.stderr)
        print("  2) Local Mongo (no Docker needed on this Mac):", file=sys.stderr)
        print("       make mongo", file=sys.stderr)
        print("     and set MONGODB_URI=mongodb://localhost:27017 in backend/.env", file=sys.stderr)
        print("", file=sys.stderr)
        return 1

    print("→ MongoDB OK", flush=True)
    return 0


def _redact(uri: str) -> str:
    if "@" not in uri:
        return uri
    # mongodb+srv://user:pass@host → mongodb+srv://***@host
    scheme, rest = uri.split("://", 1)
    creds, host = rest.rsplit("@", 1)
    return f"{scheme}://***@{host}"


if __name__ == "__main__":
    raise SystemExit(main())
