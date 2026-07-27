"""Production cookie flags for cross-origin Vercel ↔ API."""

from __future__ import annotations


def test_cookie_flags_dev(monkeypatch):
    from db.settings import get_settings

    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")
    get_settings.cache_clear()

    from api.auth.session import cookie_flags

    secure, samesite = cookie_flags()
    assert secure is False
    assert samesite == "lax"
    get_settings.cache_clear()


def test_cookie_flags_production_env(monkeypatch):
    from db.settings import get_settings

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")
    get_settings.cache_clear()

    from api.auth.session import cookie_flags

    secure, samesite = cookie_flags()
    assert secure is True
    assert samesite == "none"
    get_settings.cache_clear()


def test_cookie_flags_https_frontend(monkeypatch):
    from db.settings import get_settings

    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("FRONTEND_URL", "https://selfpi.vercel.app")
    get_settings.cache_clear()

    from api.auth.session import cookie_flags

    secure, samesite = cookie_flags()
    assert secure is True
    assert samesite == "none"
    get_settings.cache_clear()
