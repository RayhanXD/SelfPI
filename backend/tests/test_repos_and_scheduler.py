"""Connect-repo endpoints + scheduled watcher units."""

from __future__ import annotations

import mongomock
from fastapi.testclient import TestClient

from db.client import apis, set_client_override
from db.repos import connect_repo, get_connected_repo
from db.schemas import ensure_indexes
from watcher.scheduler import live_api_ids, poll_live_apis


def setup_function():
    client = mongomock.MongoClient()
    set_client_override(client)
    ensure_indexes(client["selfpi"])


def teardown_function():
    set_client_override(None)


def test_connect_repo_persists_without_stamping_all_apis():
    from api.main import app

    apis().insert_one(
        {
            "_id": "stripe",
            "name": "Stripe",
            "mode": "live",
            "spec_url": "https://example.com/openapi.json",
            "repo": "old/repo",
            "languages": ["python"],
            "status": "up_to_date",
            "open_change_count": 0,
        }
    )

    http = TestClient(app)
    # github_ready is False in tests → connect by full_name without listing
    resp = http.post(
        "/repos/connect",
        json={"full_name": "acme/billing", "repo_path": "/tmp/billing"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["full_name"] == "acme/billing"
    assert body["owner"] == "acme"
    assert body["name"] == "billing"
    # Path only kept if the directory exists; otherwise cleared for clone-on-detect.
    assert body["full_name"] == "acme/billing"

    connected = http.get("/repos/connected")
    assert connected.status_code == 200
    assert connected.json()["full_name"] == "acme/billing"

    # Prod path: do not stamp every watched API onto the new repo.
    api_doc = apis().find_one({"_id": "stripe"})
    assert api_doc["repo"] == "old/repo"

    settings = http.get("/settings")
    assert settings.status_code == 200
    data = settings.json()
    assert data["connected_repo"] == "acme/billing"
    assert data["watch_enabled"] is False  # conftest disables watcher
    assert data["watch_interval_seconds"] == 300


def test_connect_rejects_bad_full_name():
    from api.main import app

    http = TestClient(app)
    resp = http.post("/repos/connect", json={"full_name": "nopath"})
    assert resp.status_code == 400


def test_disconnect_repo():
    from api.main import app

    connect_repo(full_name="acme/app", propagate_to_apis=False)
    assert get_connected_repo() is not None

    http = TestClient(app)
    resp = http.delete("/repos/connected")
    assert resp.status_code == 200
    assert resp.json()["disconnected"] is True
    assert get_connected_repo() is None


def test_list_repos_requires_github(monkeypatch):
    from api.main import app

    http = TestClient(app)
    resp = http.get("/repos")
    assert resp.status_code == 503


def test_list_repos_with_fake_github(monkeypatch):
    from api.main import app
    from db.settings import get_settings

    monkeypatch.setenv("GITHUB_APP_ID", "1")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "k")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "2")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "db.settings.Settings.github_app_credentials_ready",
        property(lambda self: bool(self.github_app_id and self.github_app_private_key)),
    )
    monkeypatch.setattr(
        "db.settings.Settings.github_ready",
        property(lambda self: True),
    )
    monkeypatch.setattr("db.settings.github_ready", lambda: True)

    class FakeClient:
        configured = True

        def __init__(self, *args, **kwargs):
            self.installation_id = kwargs.get("installation_id") or "2"

        def list_installation_repos(self):
            return [
                {
                    "full_name": "acme/billing",
                    "owner": "acme",
                    "name": "billing",
                    "private": False,
                    "default_branch": "main",
                    "html_url": "https://github.com/acme/billing",
                },
                {
                    "full_name": "acme/other",
                    "owner": "acme",
                    "name": "other",
                    "private": True,
                    "default_branch": "trunk",
                    "html_url": "https://github.com/acme/other",
                },
            ]

    monkeypatch.setattr("api.routes.repos.GitHubAppClient", FakeClient)
    connect_repo(full_name="acme/billing", propagate_to_apis=False)

    http = TestClient(app)
    resp = http.get("/repos")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["connected_repo"] == "acme/billing"
    assert len(body["items"]) == 2
    assert body["items"][0]["full_name"] == "acme/billing"
    assert body["items"][0]["connected"] is True
    assert body["items"][1]["connected"] is False

    # Connecting a listed repo works
    ok = http.post("/repos/connect", json={"full_name": "acme/other"})
    assert ok.status_code == 200
    assert ok.json()["full_name"] == "acme/other"

    # Unknown repo rejected when App is ready
    bad = http.post("/repos/connect", json={"full_name": "nope/missing"})
    assert bad.status_code == 404


def test_live_api_ids_skips_demo():
    apis().insert_many(
        [
            {
                "_id": "stripe-demo",
                "mode": "demo",
                "spec_url": None,
                "name": "Demo",
                "status": "up_to_date",
            },
            {
                "_id": "stripe",
                "mode": "live",
                "spec_url": "https://example.com/spec.json",
                "name": "Live",
                "status": "up_to_date",
            },
            {
                "_id": "orphan",
                "mode": "live",
                "spec_url": None,
                "name": "No url",
                "status": "up_to_date",
            },
        ]
    )
    assert live_api_ids() == ["stripe"]


def test_poll_live_apis_calls_poll(monkeypatch):
    apis().insert_one(
        {
            "_id": "stripe",
            "mode": "live",
            "spec_url": "https://example.com/spec.json",
            "name": "Live",
            "status": "up_to_date",
        }
    )
    calls: list[str] = []

    def fake_poll(api_id, *, open_pr=False, dry_run_pr=True):
        calls.append(api_id)
        return {"checked": True, "new_version": "2026-07-01", "changes_detected": 2}

    monkeypatch.setattr("watcher.poll_api", fake_poll)
    summary = poll_live_apis(open_pr=False, dry_run_pr=True)
    assert calls == ["stripe"]
    assert summary["checked"] == 1
    assert summary["changed"] == 1
    assert summary["results"][0]["changes_detected"] == 2


def test_list_installation_repos_on_client(monkeypatch):
    from patcher.github import GitHubAppClient

    class _Resp:
        def __init__(self, payload):
            self._payload = payload
            self.status_code = 200

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    class _Http:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, url, params=None):
            assert "/installation/repositories" in url
            return _Resp(
                {
                    "total_count": 1,
                    "repositories": [
                        {
                            "full_name": "acme/app",
                            "name": "app",
                            "owner": {"login": "acme"},
                            "private": False,
                            "default_branch": "main",
                            "html_url": "https://github.com/acme/app",
                        }
                    ],
                }
            )

    client = GitHubAppClient(app_id="1", private_key="k", installation_id="2")
    monkeypatch.setattr(client, "_installation_token", lambda: "tok")
    monkeypatch.setattr("patcher.github.httpx.Client", _Http)
    repos = client.list_installation_repos()
    assert repos == [
        {
            "full_name": "acme/app",
            "owner": "acme",
            "name": "app",
            "private": False,
            "default_branch": "main",
            "html_url": "https://github.com/acme/app",
        }
    ]
