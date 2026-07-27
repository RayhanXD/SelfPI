"""Public Install App onboarding — discovery + sync."""

from __future__ import annotations

import mongomock
from fastapi.testclient import TestClient

from api.auth.session import COOKIE_NAME, dump_session
from db.client import set_client_override
from db.schemas import ensure_indexes
from db.settings import get_settings


def setup_function():
    client = mongomock.MongoClient()
    set_client_override(client)
    ensure_indexes(client["selfpi"])
    get_settings.cache_clear()


def teardown_function():
    set_client_override(None)
    get_settings.cache_clear()


def _restore_credentials_ready(monkeypatch):
    monkeypatch.setattr(
        "db.settings.Settings.github_app_credentials_ready",
        property(lambda self: bool(self.github_app_id and self.github_app_private_key)),
    )


def test_settings_exposes_install_fields(monkeypatch):
    from api.main import app

    monkeypatch.setenv("GITHUB_APP_ID", "4401536")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "-----BEGIN KEY-----\nok\n-----END KEY-----")
    monkeypatch.setenv("GITHUB_APP_SLUG", "selfpi")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "")
    get_settings.cache_clear()
    _restore_credentials_ready(monkeypatch)

    http = TestClient(app)
    resp = http.get("/settings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["github_configured"] is True
    assert body["app_installed"] is False
    assert body["install_url"] == "https://github.com/apps/selfpi/installations/new"


def test_me_app_installed_from_session(monkeypatch):
    from api.main import app

    monkeypatch.setenv("GITHUB_APP_ID", "1")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "k")
    monkeypatch.setenv("GITHUB_APP_SLUG", "selfpi")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "")
    get_settings.cache_clear()
    _restore_credentials_ready(monkeypatch)

    http = TestClient(app)
    token = dump_session(
        {
            "id": 1,
            "login": "ray",
            "access_token": "u-tok",
            "installation_id": "99",
        }
    )
    http.cookies.set(COOKIE_NAME, token)
    resp = http.get("/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["authenticated"] is True
    assert body["app_installed"] is True
    assert body["install_url"] == "https://github.com/apps/selfpi/installations/new"


def test_sync_installation_discovers_app(monkeypatch):
    from api.main import app

    monkeypatch.setenv("GITHUB_APP_ID", "4401536")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "k")
    monkeypatch.setenv("GITHUB_APP_SLUG", "selfpi")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "")
    get_settings.cache_clear()
    _restore_credentials_ready(monkeypatch)

    monkeypatch.setattr(
        "api.routes.auth.sync_installation_id",
        lambda session, installation_id=None: session.__setitem__(
            "installation_id", "555"
        )
        or session,
    )

    http = TestClient(app)
    token = dump_session(
        {"id": 1, "login": "ray", "access_token": "u-tok"}
    )
    http.cookies.set(COOKIE_NAME, token)
    resp = http.post("/auth/github/sync-installation")
    assert resp.status_code == 200
    body = resp.json()
    assert body["app_installed"] is True
    assert body["installation_id"] == "555"


def test_installed_callback_stores_installation(monkeypatch):
    from api.main import app

    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")
    get_settings.cache_clear()

    http = TestClient(app, follow_redirects=False)
    token = dump_session({"id": 1, "login": "ray", "access_token": "u-tok"})
    http.cookies.set(COOKIE_NAME, token)
    resp = http.get("/auth/github/installed?installation_id=777&setup_action=install")
    assert resp.status_code == 302
    assert "installed=1" in resp.headers["location"]
    # Cookie refreshed with installation_id
    set_cookie = resp.headers.get("set-cookie") or ""
    assert COOKIE_NAME in set_cookie


def test_list_repos_uses_session_installation(monkeypatch):
    from api.main import app

    monkeypatch.setenv("GITHUB_APP_ID", "1")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "k")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "c")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "s")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "")
    get_settings.cache_clear()
    _restore_credentials_ready(monkeypatch)
    monkeypatch.setattr(
        "db.settings.Settings.oauth_ready",
        property(lambda self: True),
    )
    monkeypatch.setattr(
        "db.settings.Settings.login_required",
        property(lambda self: True),
    )

    seen: dict = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            seen["installation_id"] = kwargs.get("installation_id")

        def list_installation_repos(self):
            return [
                {
                    "full_name": "acme/app",
                    "owner": "acme",
                    "name": "app",
                    "private": False,
                    "default_branch": "main",
                    "html_url": "https://github.com/acme/app",
                }
            ]

    monkeypatch.setattr("api.routes.repos.GitHubAppClient", FakeClient)

    http = TestClient(app)
    token = dump_session(
        {
            "id": 1,
            "login": "ray",
            "access_token": "u-tok",
            "installation_id": "42",
        }
    )
    http.cookies.set(COOKIE_NAME, token)
    resp = http.get("/repos")
    assert resp.status_code == 200
    assert seen["installation_id"] == "42"
    assert resp.json()["items"][0]["full_name"] == "acme/app"


def test_list_repos_app_not_installed(monkeypatch):
    from api.main import app

    monkeypatch.setenv("GITHUB_APP_ID", "1")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "k")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "c")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "s")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "")
    get_settings.cache_clear()
    _restore_credentials_ready(monkeypatch)
    monkeypatch.setattr(
        "db.settings.Settings.oauth_ready",
        property(lambda self: True),
    )
    monkeypatch.setattr(
        "db.settings.Settings.login_required",
        property(lambda self: True),
    )
    monkeypatch.setattr(
        "api.routes.repos.sync_installation_id",
        lambda session, installation_id=None: session,
    )

    http = TestClient(app)
    token = dump_session({"id": 1, "login": "ray", "access_token": "u-tok"})
    http.cookies.set(COOKIE_NAME, token)
    resp = http.get("/repos")
    assert resp.status_code == 503
    assert resp.json()["detail"]["error"]["code"] == "app_not_installed"
