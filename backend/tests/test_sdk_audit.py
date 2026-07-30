"""SDK drift audit — legacy openai 0.28 pin must surface on Check."""

from __future__ import annotations

from pathlib import Path

import mongomock

from db.client import apis, changes, set_client_override
from db.schemas import ensure_indexes
from detector.ensure import STRIPE_SPEC_URL, ensure_watched_api
from pipeline.sdk_audit import audit_consumer_sdk
from watcher import poll_api

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY = REPO_ROOT / "fixtures" / "detector" / "with_openai_legacy"


def setup_function():
    client = mongomock.MongoClient()
    set_client_override(client)
    ensure_indexes(client["selfpi"])


def teardown_function():
    set_client_override(None)


def test_consumer_versions_reads_openai_pin():
    from detector.consumer_versions import consumer_package_versions, parse_version, version_less

    vers = consumer_package_versions(LEGACY)
    assert vers["openai"] == "0.28.1"
    assert version_less(parse_version("0.28.1"), (1, 0, 0))


def test_sdk_audit_opens_legacy_openai_change():
    ensure_watched_api(
        "openai",
        repo="RayhanXD/WishBot",
        repo_path=str(LEGACY),
        languages=["python"],
    )
    # Point repo_path on the doc (ensure stores it)
    doc = apis().find_one({"_id": "openai"})
    assert doc is not None
    assert doc["repo_path"] == str(LEGACY)

    result = audit_consumer_sdk("openai")
    assert result["audited"] is True
    assert result["pinned_version"] == "0.28.1"
    assert result["changes_detected"] >= 1

    legacy = list(changes().find({"api_id": "openai", "detail.reason": "legacy_sdk"}))
    assert legacy
    assert any(c["operation_id"] == "createTranscription" for c in legacy)
    # Call site for Audio.transcribe should be found
    tx = next(c for c in legacy if c["operation_id"] == "createTranscription")
    assert len(tx.get("call_sites") or []) >= 1

    api = apis().find_one({"_id": "openai"})
    assert api["status"] == "breaking_change_unhandled"
    assert api.get("consumer_sdk_legacy") is True


def test_poll_unchanged_still_runs_sdk_audit(monkeypatch):
    """Re-check with identical upstream fingerprint must still catch legacy pins."""
    ensure_watched_api(
        "openai",
        repo="RayhanXD/WishBot",
        repo_path=str(LEGACY),
        languages=["python"],
    )
    # Pretend we already baselined upstream
    from watcher import fingerprint_spec

    tiny = {
        "openapi": "3.1.0",
        "info": {"title": "OpenAI", "version": "2.0.0"},
        "paths": {
            f"/v1/x{i}": {
                "get": {
                    "operationId": f"op{i}",
                    "responses": {"200": {"description": "OK"}},
                }
            }
            for i in range(25)
        },
    }
    from db.client import spec_versions

    spec_versions().insert_one(
        {
            "api_id": "openai",
            "version": "2.0.0",
            "fetched_at": "2026-07-01T00:00:00Z",
            "spec": tiny,
            "fingerprint": fingerprint_spec(tiny),
        }
    )
    apis().update_one(
        {"_id": "openai"},
        {"$set": {"current_version": "2.0.0", "spec_url": "https://example.com/oai.json"}},
    )

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return tiny

        text = ""
        headers = {"content-type": "application/json"}
        url = "https://example.com/oai.json"

    class _FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url):
            return _FakeResponse()

    monkeypatch.setattr("watcher.httpx.Client", lambda **kwargs: _FakeClient())

    result = poll_api("openai")
    assert result["unchanged"] is True
    assert result["changes_detected"] >= 1
    assert changes().count_documents({"api_id": "openai", "detail.reason": "legacy_sdk"}) >= 1
