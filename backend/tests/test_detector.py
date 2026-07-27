"""API auto-detection from a local repo checkout (v1: Python + Stripe).

Fixture layout under fixtures/detector/<case>/ with expected.json:
  { "detected_apis": ["stripe"] }  or  { "detected_apis": [] }
"""

from __future__ import annotations

import json
from pathlib import Path

import mongomock

from db.client import apis, set_client_override
from db.schemas import ensure_indexes
from detector import detect_and_ensure, detect_apis
from detector.ensure import STRIPE_SPEC_URL, ensure_stripe
from languages.python.detect_apis import detect_stripe

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "fixtures" / "detector"


def setup_function():
    client = mongomock.MongoClient()
    set_client_override(client)
    ensure_indexes(client["selfpi"])


def teardown_function():
    set_client_override(None)


def _cases():
    return sorted(p for p in FIXTURES.iterdir() if p.is_dir() and (p / "expected.json").is_file())


def test_fixture_detection_matrix():
    assert _cases(), "expected detector fixtures under fixtures/detector/"
    for case in _cases():
        expected = json.loads((case / "expected.json").read_text())["detected_apis"]
        got = detect_apis(case)
        assert got == expected, f"{case.name}: got {got!r} expected {expected!r}"


def test_detect_stripe_helper_on_with_without():
    assert detect_stripe(FIXTURES / "with_stripe") is True
    assert detect_stripe(FIXTURES / "without_stripe") is False


def test_ensure_stripe_creates_live_doc():
    ensured = ensure_stripe(repo="acme/billing", repo_path="/tmp/billing")
    assert ensured == "stripe"
    doc = apis().find_one({"_id": "stripe"})
    assert doc is not None
    assert doc["mode"] == "live"
    assert doc["spec_url"] == STRIPE_SPEC_URL
    assert doc["languages"] == ["python"]
    assert doc["repo"] == "acme/billing"
    assert doc["repo_path"] == "/tmp/billing"


def test_ensure_stripe_updates_existing_does_not_duplicate():
    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "mode": "live",
            "spec_url": "https://old.example/spec.json",
            "repo": "old/repo",
            "languages": [],
            "status": "up_to_date",
            "open_change_count": 0,
            "current_version": "2026-01-01",
        }
    )
    apis().insert_one(
        {
            "_id": "stripe-demo",
            "name": "Stripe (demo)",
            "mode": "demo",
            "spec_url": None,
            "repo": "old/repo",
            "languages": ["python"],
            "status": "up_to_date",
            "open_change_count": 0,
        }
    )

    ensure_stripe(repo="acme/billing", repo_path="/tmp/billing")

    assert apis().count_documents({"_id": "stripe"}) == 1
    doc = apis().find_one({"_id": "stripe"})
    assert doc["spec_url"] == STRIPE_SPEC_URL
    assert doc["repo"] == "acme/billing"
    assert doc["repo_path"] == "/tmp/billing"
    assert doc["languages"] == ["python"]
    assert doc["mode"] == "live"
    # Preserve version baseline — do not wipe on stamp
    assert doc["current_version"] == "2026-01-01"

    demo = apis().find_one({"_id": "stripe-demo"})
    assert demo is not None
    assert demo["mode"] == "demo"
    assert demo["repo"] == "old/repo"  # ensure_stripe does not touch demo


def test_detect_and_ensure_with_fixture_tree():
    result = detect_and_ensure(
        repo="acme/billing",
        repo_path=FIXTURES / "with_stripe",
    )
    assert result["detected_apis"] == ["stripe"]
    assert result["ensured"] == ["stripe"]
    assert result["repo_path"] is not None
    doc = apis().find_one({"_id": "stripe"})
    assert doc["mode"] == "live"
    assert doc["spec_url"] == STRIPE_SPEC_URL


def test_detect_and_ensure_without_stripe_creates_nothing():
    result = detect_and_ensure(
        repo="acme/other",
        repo_path=FIXTURES / "without_stripe",
    )
    assert result["detected_apis"] == []
    assert result["ensured"] == []
    assert apis().find_one({"_id": "stripe"}) is None


def test_connect_returns_detected_apis():
    from api.main import app
    from fastapi.testclient import TestClient

    http = TestClient(app)
    resp = http.post(
        "/repos/connect",
        json={
            "full_name": "acme/billing",
            "repo_path": str(FIXTURES / "with_stripe"),
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["full_name"] == "acme/billing"
    assert body["detected_apis"] == ["stripe"]

    doc = apis().find_one({"_id": "stripe"})
    assert doc is not None
    assert doc["mode"] == "live"
    assert doc["repo"] == "acme/billing"
    assert doc["spec_url"] == STRIPE_SPEC_URL

    # demo fixture untouched (not present) — reconnect without stripe leaves stripe if already ensured
    resp2 = http.post(
        "/repos/connect",
        json={
            "full_name": "acme/other",
            "repo_path": str(FIXTURES / "without_stripe"),
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["detected_apis"] == []


def test_detect_endpoint_reruns():
    from api.main import app
    from fastapi.testclient import TestClient

    http = TestClient(app)
    # No connected repo → 404
    missing = http.post("/repos/connected/detect")
    assert missing.status_code == 404

    http.post(
        "/repos/connect",
        json={
            "full_name": "acme/billing",
            "repo_path": str(FIXTURES / "with_stripe"),
        },
    )
    # Wipe live api to prove re-detect re-ensures
    apis().delete_one({"_id": "stripe"})

    again = http.post("/repos/connected/detect")
    assert again.status_code == 200, again.text
    body = again.json()
    assert body["detected_apis"] == ["stripe"]
    assert body["ensured"] == ["stripe"]
    assert apis().find_one({"_id": "stripe"}) is not None
