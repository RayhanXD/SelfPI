"""GitHub App user-to-server OAuth helpers."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from db.settings import get_settings

AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_URL = "https://api.github.com"


def authorize_url(*, state: str) -> str:
    s = get_settings()
    if not s.oauth_ready:
        raise RuntimeError("GitHub OAuth not configured (GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET)")
    params = {
        "client_id": s.github_client_id,
        "redirect_uri": s.github_oauth_redirect_uri,
        "state": state,
        "allow_signup": "true",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(code: str) -> str:
    """Exchange OAuth code for a user access token. Returns the token string."""
    s = get_settings()
    if not s.oauth_ready:
        raise RuntimeError("GitHub OAuth not configured")
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(
            TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": s.github_client_id,
                "client_secret": s.github_client_secret,
                "code": code,
                "redirect_uri": s.github_oauth_redirect_uri,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(data.get("error_description") or data.get("error") or "No access_token")
    return str(token)


def _user_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_github_user(access_token: str) -> dict[str, Any]:
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{API_URL}/user", headers=_user_headers(access_token))
        resp.raise_for_status()
        return resp.json()


def list_user_installations(access_token: str) -> list[dict[str, Any]]:
    """Installations the user can manage (`GET /user/installations`)."""
    installations: list[dict[str, Any]] = []
    page = 1
    with httpx.Client(timeout=10.0, headers=_user_headers(access_token)) as client:
        while True:
            resp = client.get(
                f"{API_URL}/user/installations",
                params={"per_page": 100, "page": page},
            )
            resp.raise_for_status()
            data = resp.json()
            batch = data.get("installations") or []
            installations.extend(batch)
            total = int(data.get("total_count") or 0)
            if len(installations) >= total or not batch:
                break
            page += 1
    return installations


def find_app_installation(access_token: str, app_id: str) -> dict[str, Any] | None:
    """Return the installation of `app_id` for this user, if any."""
    want = str(app_id)
    for inst in list_user_installations(access_token):
        if str(inst.get("app_id") or "") == want:
            return inst
    return None
