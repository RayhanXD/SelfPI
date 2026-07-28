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


def test_github_login_stores_next_and_redirects(monkeypatch):
    from api.auth.session import sanitize_post_login_path
    from api.main import app
    from db.settings import get_settings

    monkeypatch.setenv("GITHUB_CLIENT_ID", "Iv1.client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "db.settings.Settings.oauth_ready",
        property(lambda self: True),
    )

    http = TestClient(app, follow_redirects=False)
    resp = http.get("/auth/github/login?next=/app/settings")
    assert resp.status_code == 302
    assert "github.com/login/oauth/authorize" in resp.headers["location"]
    set_cookie = resp.headers.get("set-cookie") or ""
    # Starlette may emit multiple Set-Cookie; TestClient joins or keeps jar.
    assert "selfpi_oauth_state=" in (set_cookie + str(http.cookies))
    raw_next = http.cookies.get("selfpi_oauth_next")
    assert sanitize_post_login_path(raw_next) == "/app/settings"


def test_sanitize_rejects_open_redirect():
    from api.auth.session import sanitize_post_login_path

    assert sanitize_post_login_path("/app/changes") == "/app/changes"
    assert sanitize_post_login_path("https://evil.example/") == "/app"
    assert sanitize_post_login_path("//evil.example") == "/app"
    assert sanitize_post_login_path("/auth/callback") == "/app"
    assert sanitize_post_login_path('"/app/settings"') == "/app/settings"


def test_handoff_exchange_sets_session(monkeypatch):
    from api.auth.session import create_handoff_token, load_session
    from api.main import app
    from db.settings import get_settings

    monkeypatch.setenv("SESSION_SECRET", "test-secret-handoff")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "Iv1.client")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "secret")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "db.settings.Settings.oauth_ready",
        property(lambda self: True),
    )

    session = {
        "id": 42,
        "login": "octo",
        "name": "Octo",
        "avatar_url": None,
        "html_url": "https://github.com/octo",
        "access_token": "ghu_test",
    }
    handoff = create_handoff_token(session)

    http = TestClient(app)
    resp = http.post("/auth/handoff", json={"handoff": handoff})
    assert resp.status_code == 200
    body = resp.json()
    assert body["authenticated"] is True
    assert body["user"]["login"] == "octo"
    assert body["session_token"]
    loaded = load_session(body["session_token"])
    assert loaded is not None
    assert loaded["login"] == "octo"

    # Bearer works without cookie
    http2 = TestClient(app)
    me = http2.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {body['session_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["authenticated"] is True
    assert me.json()["user"]["login"] == "octo"

    bad = http.post("/auth/handoff", json={"handoff": "not-a-real-token"})
    assert bad.status_code == 401


def test_bearer_read_session(monkeypatch):
    from api.auth.session import dump_session
    from api.main import app
    from db.settings import get_settings

    monkeypatch.setenv("SESSION_SECRET", "test-secret-bearer")
    get_settings.cache_clear()

    token = dump_session({"id": 1, "login": "ray", "name": "Ray"})
    http = TestClient(app)
    resp = http.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["authenticated"] is True
    assert resp.json()["user"]["login"] == "ray"
