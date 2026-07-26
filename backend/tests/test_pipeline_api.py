"""M4 integration — spec bump → changes with embedded call sites (mongomock)."""

from __future__ import annotations

import json
from pathlib import Path

import mongomock
from fastapi.testclient import TestClient

from db.client import set_client_override
from db.schemas import ensure_indexes

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "fixtures"


def _load(path: Path):
    return json.loads(path.read_text())


def setup_function():
    client = mongomock.MongoClient()
    set_client_override(client)
    ensure_indexes(client["selfpi"])


def teardown_function():
    set_client_override(None)


def _seed_api_with_old_spec(client: TestClient):
    old = _load(FIXTURES / "diff" / "renamed_param" / "old.json")
    # Create via DB directly for control
    from db.client import apis, spec_versions

    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "spec_url": "https://example.com/openapi.json",
            "repo": "myorg/billing-app",
            "repo_path": str(FIXTURES / "sample_repo"),
            "languages": ["python"],
            "current_version": "2026-06-01",
            "status": "up_to_date",
            "last_checked": "2026-06-01T00:00:00Z",
            "open_change_count": 0,
        }
    )
    spec_versions().insert_one(
        {
            "api_id": "stripe",
            "version": "2026-06-01",
            "fetched_at": "2026-06-01T00:00:00Z",
            "spec": old,
            "fingerprint": "old",
        }
    )


def test_bump_creates_change_with_call_sites():
    from api.main import app

    http = TestClient(app)
    _seed_api_with_old_spec(http)

    new = _load(FIXTURES / "diff" / "renamed_param" / "new.json")
    resp = http.post(
        "/apis/stripe/spec-versions",
        json={"version": "2026-07-01", "spec": new},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["version"] == "2026-07-01"
    assert body["changes_detected"] == 1

    feed = http.get("/changes", params={"api_id": "stripe"})
    assert feed.status_code == 200
    items = feed.json()["items"]
    assert len(items) == 1
    assert items[0]["operation_id"] == "createCharge"
    assert items[0]["kind"] == "renamed_param"
    assert items[0]["call_site_count"] == 2
    assert items[0]["status"] == "detected"

    detail = http.get(f"/changes/{items[0]['id']}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["spec_diff"]["removed"] == ["source"]
    assert data["spec_diff"]["added"] == ["payment_method"]
    assert len(data["call_sites"]) == 2
    assert all(cs["operation_id"] == "createCharge" for cs in data["call_sites"])

    api = http.get("/apis/stripe")
    assert api.json()["status"] == "breaking_change_unhandled"
    assert api.json()["open_change_count"] == 1
    assert api.json()["current_version"] == "2026-07-01"


def test_dismiss_clears_open_count():
    from api.main import app

    http = TestClient(app)
    _seed_api_with_old_spec(http)
    new = _load(FIXTURES / "diff" / "renamed_param" / "new.json")
    http.post("/apis/stripe/spec-versions", json={"version": "2026-07-01", "spec": new})
    change_id = http.get("/changes").json()["items"][0]["id"]

    resp = http.post(f"/changes/{change_id}/dismiss")
    assert resp.status_code == 200
    assert resp.json()["status"] == "dismissed"

    api = http.get("/apis/stripe").json()
    assert api["open_change_count"] == 0
    assert api["status"] == "up_to_date"


def test_rescan_reruns_scanner():
    from api.main import app

    http = TestClient(app)
    _seed_api_with_old_spec(http)
    new = _load(FIXTURES / "diff" / "renamed_param" / "new.json")
    http.post("/apis/stripe/spec-versions", json={"version": "2026-07-01", "spec": new})
    change_id = http.get("/changes").json()["items"][0]["id"]

    resp = http.post(f"/changes/{change_id}/rescan")
    assert resp.status_code == 200
    assert resp.json()["call_site_count"] == 2
    assert resp.json()["status"] == "detected"
