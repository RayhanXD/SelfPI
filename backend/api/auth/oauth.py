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
    with httpx.Client(timeout=30.0) as client:
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


def fetch_github_user(access_token: str) -> dict[str, Any]:
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            f"{API_URL}/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        resp.raise_for_status()
        return resp.json()
