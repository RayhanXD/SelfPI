"""Isolate tests from a developer machine's real GitHub App .env."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_github_app_in_tests(monkeypatch):
    """Pipeline tests must not open real PRs / report GitHub ready when .env has creds."""
    monkeypatch.setenv("GITHUB_APP_ID", "")
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "")
    monkeypatch.setenv("GITHUB_APP_INSTALLATION_ID", "")
    monkeypatch.setenv("GITHUB_DEFAULT_BASE_BRANCH", "")
    monkeypatch.setenv("GITHUB_CLIENT_ID", "")
    monkeypatch.setenv("GITHUB_CLIENT_SECRET", "")
    monkeypatch.setenv("AUTH_REQUIRED", "false")
    # Keep the scheduled watcher off during TestClient lifespan
    monkeypatch.setenv("WATCH_ENABLED", "false")
    monkeypatch.setenv("WATCH_INTERVAL_SECONDS", "300")

    from db.settings import get_settings

    get_settings.cache_clear()

    monkeypatch.setattr("db.settings.github_ready", lambda: False)
    monkeypatch.setattr("db.settings.pr_pipeline_flags", lambda: (False, True))

    # Settings.github_ready is a property used by GET /settings
    monkeypatch.setattr(
        "db.settings.Settings.github_ready",
        property(lambda self: False),
    )
    get_settings.cache_clear()
