"""Live API first-run baseline / noise control."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import mongomock

from db.client import apis, changes, set_client_override, spec_versions
from db.schemas import ensure_indexes
from pipeline.process import is_comparable_baseline, operation_count
from watcher import fingerprint_spec, poll_api

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "fixtures"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def setup_function():
    client = mongomock.MongoClient()
    set_client_override(client)
    ensure_indexes(client["selfpi"])


def teardown_function():
    set_client_override(None)


def _tiny_spec(*, version: str = "2026-06-01") -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "Stripe (demo)", "version": version},
        "paths": {
            "/v1/charges": {
                "post": {
                    "operationId": "createCharge",
                    "parameters": [
                        {
                            "name": "source",
                            "in": "query",
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            }
        },
    }


def _fullish_spec(*, version: str = "2026-07-01") -> dict[str, Any]:
    """Large enough to trip the live comparable-baseline heuristic vs a 1-op demo."""
    paths: dict[str, Any] = {}
    for i in range(25):
        paths[f"/v1/resource_{i}"] = {
            "get": {
                "operationId": f"getResource{i}",
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "operationId": f"createResource{i}",
                "parameters": [
                    {
                        "name": "source",
                        "in": "query",
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "OK"}},
            },
        }
    return {
        "openapi": "3.1.0",
        "info": {"title": "Stripe", "version": version},
        "paths": paths,
    }


def _insert_live_api(*, current_version: str | None = None) -> None:
    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "mode": "live",
            "spec_url": "https://example.com/openapi.json",
            "repo": "myorg/billing-app",
            "repo_path": str(FIXTURES / "sample_repo"),
            "languages": ["python"],
            "current_version": current_version,
            "status": "up_to_date",
            "last_checked": None,
            "open_change_count": 0,
        }
    )


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    def __init__(self, payload: dict[str, Any]):
        self._payload = payload
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url: str):
        self.calls += 1
        return _FakeResponse(self._payload)


def test_operation_count_and_comparable_baseline():
    tiny = _tiny_spec()
    full = _fullish_spec()
    assert operation_count(tiny) == 1
    assert operation_count(full) == 50
    assert is_comparable_baseline(tiny, full) is False
    assert is_comparable_baseline(full, full) is True
    # Same-scale fixture diffs remain comparable
    old = _load(FIXTURES / "diff" / "renamed_param" / "old.json")
    new = _load(FIXTURES / "diff" / "renamed_param" / "new.json")
    assert is_comparable_baseline(old, new) is True


def test_first_poll_baselines_without_changes(monkeypatch):
    _insert_live_api()
    spec = _fullish_spec(version="2026-07-01")
    fake = _FakeClient(spec)
    monkeypatch.setattr("watcher.httpx.Client", lambda **kwargs: fake)

    result = poll_api("stripe")
    assert result["checked"] is True
    assert result["new_version"] == "2026-07-01"
    assert result["changes_detected"] == 0
    assert result["baseline"] is True

    stored = list(spec_versions().find({"api_id": "stripe"}))
    assert len(stored) == 1
    assert stored[0]["version"] == "2026-07-01"
    assert stored[0]["fingerprint"] == fingerprint_spec(spec)
    assert changes().count_documents({"api_id": "stripe"}) == 0
    api = apis().find_one({"_id": "stripe"})
    assert api["current_version"] == "2026-07-01"
    assert api["status"] == "up_to_date"


def test_second_identical_poll_is_noop(monkeypatch):
    _insert_live_api()
    spec = _fullish_spec(version="2026-07-01")
    fake = _FakeClient(spec)
    monkeypatch.setattr("watcher.httpx.Client", lambda **kwargs: fake)

    first = poll_api("stripe")
    assert first["baseline"] is True
    assert first["changes_detected"] == 0

    second = poll_api("stripe")
    assert second["checked"] is True
    assert second["new_version"] is None
    assert second["changes_detected"] == 0
    assert second["baseline"] is False
    assert second["unchanged"] is True
    assert spec_versions().count_documents({"api_id": "stripe"}) == 1
    assert changes().count_documents({"api_id": "stripe"}) == 0


def test_third_poll_with_real_diff_creates_changes(monkeypatch):
    _insert_live_api()
    baseline = _fullish_spec(version="2026-07-01")
    bumped = copy.deepcopy(baseline)
    bumped["info"]["version"] = "2026-07-02"
    # Rename a param on one operation so the diff engine emits a change.
    bumped["paths"]["/v1/resource_0"]["post"]["parameters"][0]["name"] = "payment_method"

    payloads = [baseline, baseline, bumped]
    call_idx = {"i": 0}

    class _SequencedClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url: str):
            idx = call_idx["i"]
            call_idx["i"] += 1
            return _FakeResponse(payloads[min(idx, len(payloads) - 1)])

    monkeypatch.setattr("watcher.httpx.Client", lambda **kwargs: _SequencedClient())

    assert poll_api("stripe")["baseline"] is True
    assert poll_api("stripe")["new_version"] is None

    third = poll_api("stripe")
    assert third["baseline"] is False
    assert third["new_version"] == "2026-07-02"
    assert third["changes_detected"] >= 1
    assert changes().count_documents({"api_id": "stripe"}) >= 1


def test_live_tiny_prior_is_rebaselined(monkeypatch):
    """Demo tiny spec accidentally on live API must not create thousands of removals."""
    _insert_live_api(current_version="2026-06-01")
    tiny = _tiny_spec()
    spec_versions().insert_one(
        {
            "api_id": "stripe",
            "version": "2026-06-01",
            "fetched_at": "2026-06-01T00:00:00Z",
            "spec": tiny,
            "fingerprint": fingerprint_spec(tiny),
        }
    )
    full = _fullish_spec(version="2026-07-01")
    monkeypatch.setattr("watcher.httpx.Client", lambda **kwargs: _FakeClient(full))

    result = poll_api("stripe")
    assert result["baseline"] is True
    assert result["changes_detected"] == 0
    assert changes().count_documents({"api_id": "stripe"}) == 0
    assert spec_versions().count_documents({"api_id": "stripe"}) == 2
    assert apis().find_one({"_id": "stripe"})["current_version"] == "2026-07-01"


def test_check_endpoint_exposes_baseline(monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    _insert_live_api()
    spec = _fullish_spec(version="2026-07-01")
    monkeypatch.setattr("watcher.httpx.Client", lambda **kwargs: _FakeClient(spec))

    http = TestClient(app)
    resp = http.post("/apis/stripe/check")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["checked"] is True
    assert body["new_version"] == "2026-07-01"
    assert body["changes_detected"] == 0
    assert body["baseline"] is True
    assert body["unchanged"] is False
