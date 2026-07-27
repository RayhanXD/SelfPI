"""Resolve GitHub App installations for the signed-in user."""

from __future__ import annotations

from typing import Any

from api.auth.oauth import find_app_installation, list_user_installations
from db.repos import get_connected_repo
from db.settings import get_settings
from patcher.github import GitHubAppClient

# Avoid calling GitHub on every /auth/me — cache slug after first successful lookup.
_cached_app_slug: str | None = None


def _resolved_slug(*, allow_network: bool = True) -> str | None:
    global _cached_app_slug
    s = get_settings()
    slug = (s.github_app_slug or "").strip() or _cached_app_slug
    if slug:
        _cached_app_slug = slug
        return slug
    if not allow_network or not s.github_app_credentials_ready:
        return None
    try:
        info = GitHubAppClient().get_app_info()
        slug = (info.get("slug") or "").strip() or None
    except Exception:
        return None
    if slug:
        _cached_app_slug = slug
    return slug


def install_url(*, allow_network: bool = True) -> str | None:
    """Public install URL for strangers: https://github.com/apps/{slug}/installations/new.

    Hot paths (e.g. /auth/me) should pass allow_network=False so a slow GitHub
    call cannot block session checks for tens of seconds.
    """
    s = get_settings()
    if not s.github_app_credentials_ready:
        return None
    slug = _resolved_slug(allow_network=allow_network)
    if not slug:
        # Frontend resolves this against the API origin; github_install may network.
        return "/auth/github/install"
    return f"https://github.com/apps/{slug}/installations/new"


def resolve_installation_id(session: dict[str, Any] | None = None) -> str | None:
    """Prefer session → connected workspace → env fallback."""
    if session and session.get("installation_id"):
        return str(session["installation_id"])
    connected = get_connected_repo()
    if connected and connected.get("installation_id"):
        return str(connected["installation_id"])
    s = get_settings()
    if s.github_app_installation_id:
        return str(s.github_app_installation_id)
    return None


def sync_installation_id(
    session: dict[str, Any],
    *,
    installation_id: str | None = None,
) -> dict[str, Any]:
    """Attach installation_id to the session dict (mutates and returns it).

    When `installation_id` is omitted, discover via the user access token
    (`GET /user/installations` filtered to this App).
    """
    s = get_settings()
    if installation_id:
        session["installation_id"] = str(installation_id)
        return session

    token = session.get("access_token")
    if not token or not s.github_app_id:
        return session

    found = find_app_installation(str(token), str(s.github_app_id))
    if found and found.get("id") is not None:
        session["installation_id"] = str(found["id"])
    elif "installation_id" in session and not s.github_app_installation_id:
        # Keep prior session value unless we explicitly cleared
        pass
    return session


def installation_status(session: dict[str, Any] | None) -> dict[str, Any]:
    """Public fields for /settings and /auth/me.

    Never does a GitHub network round-trip — keep session checks snappy.
    """
    s = get_settings()
    iid = resolve_installation_id(session)
    return {
        "github_app_ready": s.github_app_credentials_ready,
        "app_installed": bool(iid),
        "install_url": install_url(allow_network=False),
        "installation_id": iid,
    }


def user_installations_for_app(access_token: str) -> list[dict[str, Any]]:
    """Installations of *this* App visible to the user (usually 0 or 1)."""
    s = get_settings()
    if not s.github_app_id:
        return []
    app_id = str(s.github_app_id)
    return [
        inst
        for inst in list_user_installations(access_token)
        if str(inst.get("app_id") or "") == app_id
    ]
