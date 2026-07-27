"""GitHub OAuth login — session + gated /repos."""

from __future__ import annotations

import mongomock
from fastapi.testclient import TestClient

from api.auth.session import COOKIE_NAME, dump_session
from db.client import set_client_override
from db.schemas import ensure_indexes


def setup_function():
    client = mongomock.MongoClient()
    set_client_override(client)
    ensure_indexes(client["selfpi"])


def teardown_function():
    set_client_override(None)


def test_me_unauthenticated():
    from api.main import app

    http = TestClient(app)
    resp = http.get("/auth/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["authenticated"] is False
    assert body["oauth_configured"] is False


def test_repos_require_login_when_oauth_configured(monkeypatch):
    from api.main import app
    from db.settings import get_settings

    monkeypatch.setenv("GITHUB_CLIENT_ID", "Iv1.client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "db.settings.Settings.oauth_ready",
        property(lambda self: True),
    )
    monkeypatch.setattr(
        "db.settings.Settings.login_required",
        property(lambda self: True),
    )

    http = TestClient(app)
    resp = http.get("/repos")
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"]["code"] == "login_required"


def test_repos_ok_with_session_cookie(monkeypatch):
    from api.main import app
    from db.settings import get_settings

    monkeypatch.setenv("GITHUB_CLIENT_ID", "Iv1.client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "db.settings.Settings.oauth_ready",
        property(lambda self: True),
    )
    monkeypatch.setattr(
        "db.settings.Settings.login_required",
        property(lambda self: True),
    )
    monkeypatch.setattr(
        "db.settings.Settings.github_ready",
        property(lambda self: False),
    )
    monkeypatch.setattr(
        "db.settings.Settings.github_app_credentials_ready",
        property(lambda self: False),
    )

    http = TestClient(app)
    token = dump_session(
        {"id": 1, "login": "ray", "name": "Ray", "avatar_url": None, "html_url": None}
    )
    http.cookies.set(COOKIE_NAME, token)

    # App credentials missing → 503 after auth passes
    resp = http.get("/repos")
    assert resp.status_code == 503


def test_logout_clears_cookie(monkeypatch):
    from api.main import app
    from db.settings import get_settings

    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    get_settings.cache_clear()

    http = TestClient(app)
    token = dump_session({"id": 1, "login": "ray"})
    http.cookies.set(COOKIE_NAME, token)
    resp = http.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["logged_out"] is True
