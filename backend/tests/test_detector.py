"""API auto-detection from a local repo checkout (catalog-driven).

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
from detector.ensure import STRIPE_SPEC_URL, ensure_stripe, ensure_watched_api
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
    assert doc["source"] == "detected"


def test_ensure_openai_from_catalog():
    ensured = ensure_watched_api("openai", repo="acme/ai", repo_path="/tmp/ai")
    assert ensured == "openai"
    doc = apis().find_one({"_id": "openai"})
    assert doc["name"] == "OpenAI"
    assert doc["mode"] == "live"
    assert "openai-openapi" in doc["spec_url"]


def test_ensure_anthropic_from_catalog():
    ensured = ensure_watched_api("anthropic", repo="acme/ai", repo_path="/tmp/ai")
    assert ensured == "anthropic"
    doc = apis().find_one({"_id": "anthropic"})
    assert doc["name"] == "Anthropic"
    assert doc["mode"] == "live"
    assert "anthropic-openapi-spec" in doc["spec_url"]


def test_ensure_unwatchable_skipped():
    """Catalog hits without a public OpenAPI URL are not auto-watched."""
    assert ensure_watched_api("braintree", repo="acme/pay") is None
    assert apis().find_one({"_id": "braintree"}) is None
    assert ensure_watched_api("aws", repo="acme/infra") is None


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


def test_detect_and_ensure_multi_ensures_all_watchable():
    result = detect_and_ensure(
        repo="acme/multi",
        repo_path=FIXTURES / "with_multi",
    )
    assert result["detected_apis"] == ["openai", "stripe", "twilio"]
    assert set(result["ensured"]) == {"openai", "stripe", "twilio"}
    assert apis().find_one({"_id": "openai"})["repo"] == "acme/multi"
    assert apis().find_one({"_id": "twilio"})["repo"] == "acme/multi"


def test_detect_and_ensure_ai_stack():
    result = detect_and_ensure(
        repo="acme/llm",
        repo_path=FIXTURES / "with_ai_stack",
    )
    assert result["detected_apis"] == ["anthropic", "cohere", "openai"]
    assert set(result["ensured"]) == {"anthropic", "cohere", "openai"}
    assert result["unwatchable"] == []


def test_detect_and_ensure_github_fixture():
    result = detect_and_ensure(
        repo="acme/tools",
        repo_path=FIXTURES / "with_github",
    )
    assert result["detected_apis"] == ["github"]
    assert result["ensured"] == ["github"]
    doc = apis().find_one({"_id": "github"})
    assert doc["repo"] == "acme/tools"
    assert doc["source"] == "detected"


def test_detect_and_ensure_ts_raygent_stack():
    """TS repos using raw GitHub fetch + NIM + LangChain must surface."""
    result = detect_and_ensure(
        repo="RayhanXD/raygent",
        repo_path=FIXTURES / "with_ts_raygent",
        clone=False,
    )
    assert result["detected_apis"] == ["github", "langchain", "nvidia"]
    assert result["ensured"] == ["github", "langchain", "nvidia"]
    assert result["unwatchable"] == []
    doc = apis().find_one({"_id": "github"})
    assert doc is not None
    assert doc["repo"] == "RayhanXD/raygent"
    assert "typescript" in doc.get("languages", [])
    assert apis().find_one({"_id": "langchain"})["source"] == "detected"
    assert apis().find_one({"_id": "nvidia"})["spec_url"]


def test_detect_and_ensure_detaches_undetected():
    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "mode": "live",
            "spec_url": STRIPE_SPEC_URL,
            "repo": "acme/other",
            "source": "detected",
            "status": "up_to_date",
            "open_change_count": 0,
        }
    )
    result = detect_and_ensure(
        repo="acme/other",
        repo_path=FIXTURES / "without_stripe",
    )
    assert result["detected_apis"] == []
    assert result["ensured"] == []
    doc = apis().find_one({"_id": "stripe"})
    assert doc.get("repo") in (None, "")


def test_detect_and_ensure_without_stripe_creates_nothing():
    result = detect_and_ensure(
        repo="acme/other",
        repo_path=FIXTURES / "without_stripe",
    )
    assert result["detected_apis"] == []
    assert result["ensured"] == []
    assert apis().find_one({"_id": "stripe"}) is None


def test_list_apis_workspace_filters_to_connected_repo():
    from api.main import app
    from db.repos import connect_repo
    from fastapi.testclient import TestClient

    connect_repo(full_name="acme/real", propagate_to_apis=False)
    apis().insert_one(
        {
            "_id": "stripe-demo",
            "name": "Stripe (demo)",
            "mode": "demo",
            "source": "seed",
            "repo": "RayhanXD/selfpi-demo-consumer",
            "status": "up_to_date",
            "open_change_count": 0,
            "languages": [],
        }
    )
    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "mode": "live",
            "source": "seed",
            "repo": "RayhanXD/selfpi-demo-consumer",
            "status": "up_to_date",
            "open_change_count": 0,
            "languages": [],
        }
    )
    apis().insert_one(
        {
            "_id": "openai",
            "name": "OpenAI",
            "mode": "live",
            "source": "detected",
            "repo": "acme/real",
            "status": "up_to_date",
            "open_change_count": 0,
            "languages": ["python"],
        }
    )

    http = TestClient(app)
    resp = http.get("/apis")
    assert resp.status_code == 200
    ids = {a["id"] for a in resp.json()}
    # Connected to acme/real → only openai; seed/demo harness hidden
    assert ids == {"openai"}


def test_list_changes_hides_seed_stripe_for_real_workspace():
    """Needs-review must not leak leftover Stripe seed/demo change docs."""
    from api.main import app
    from db.client import changes
    from db.repos import connect_repo
    from fastapi.testclient import TestClient

    connect_repo(full_name="acme/real", propagate_to_apis=False)
    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "mode": "live",
            "source": "seed",
            "repo": "RayhanXD/selfpi-demo-consumer",
            "status": "breaking_change_unhandled",
            "open_change_count": 1,
            "languages": ["python"],
        }
    )
    apis().insert_one(
        {
            "_id": "openai",
            "name": "OpenAI",
            "mode": "live",
            "source": "detected",
            "repo": "acme/real",
            "status": "breaking_change_unhandled",
            "open_change_count": 1,
            "languages": ["python"],
        }
    )
    changes().insert_one(
        {
            "api_id": "stripe",
            "operation_id": "createCharge",
            "kind": "renamed_param",
            "detail": {},
            "status": "detected",
            "call_sites": [],
            "detected_at": "2026-07-01T00:00:00Z",
        }
    )
    changes().insert_one(
        {
            "api_id": "openai",
            "operation_id": "createChatCompletion",
            "kind": "removed_field",
            "detail": {},
            "status": "detected",
            "call_sites": [],
            "detected_at": "2026-07-02T00:00:00Z",
        }
    )

    http = TestClient(app)
    feed = http.get("/changes")
    assert feed.status_code == 200
    items = feed.json()["items"]
    assert len(items) == 1
    assert items[0]["api_id"] == "openai"
    assert items[0]["operation_id"] == "createChatCompletion"

    # Explicit api_id for a hidden harness API still returns empty in workspace scope
    leaked = http.get("/changes", params={"api_id": "stripe"})
    assert leaked.status_code == 200
    assert leaked.json()["items"] == []

    # Debug scope still sees everything
    all_feed = http.get("/changes", params={"scope": "all"})
    assert {c["api_id"] for c in all_feed.json()["items"]} == {"stripe", "openai"}


def test_seed_apis_hidden_when_no_repo_connected():
    from api.main import app
    from fastapi.testclient import TestClient

    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "mode": "live",
            "source": "seed",
            "repo": "RayhanXD/selfpi-demo-consumer",
            "status": "up_to_date",
            "open_change_count": 0,
            "languages": [],
        }
    )
    http = TestClient(app)
    assert http.get("/apis").json() == []
    assert http.get("/apis", params={"scope": "all"}).json()[0]["id"] == "stripe"


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
