"""Signed cookie session for GitHub OAuth users."""

from __future__ import annotations

import json
from typing import Any, Literal

from itsdangerous import BadSignature, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import Response

from db.settings import get_settings

COOKIE_NAME = "selfpi_session"
SameSite = Literal["lax", "strict", "none"]


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().session_secret, salt="selfpi-auth")


def dump_session(data: dict[str, Any]) -> str:
    return _serializer().dumps(data)


def load_session(token: str) -> dict[str, Any] | None:
    try:
        raw = _serializer().loads(token)
    except BadSignature:
        return None
    return raw if isinstance(raw, dict) else None


def read_session(request: Request) -> dict[str, Any] | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return load_session(token)


def cookie_flags() -> tuple[bool, SameSite]:
    """Return (secure, samesite) for auth cookies.

    Cross-origin Vercel → API needs SameSite=None + Secure so credentials:include
    sends the session cookie. Localhost keeps Lax + insecure.
    """
    s = get_settings()
    if s.is_production:
        return True, "none"
    return False, "lax"


def set_session_cookie(response: Response, data: dict[str, Any]) -> None:
    secure, samesite = cookie_flags()
    response.set_cookie(
        COOKIE_NAME,
        dump_session(data),
        httponly=True,
        samesite=samesite,
        secure=secure,
        max_age=60 * 60 * 24 * 14,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    secure, samesite = cookie_flags()
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        secure=secure,
        samesite=samesite,
    )


def set_oauth_state_cookie(response: Response, state: str) -> None:
    secure, samesite = cookie_flags()
    response.set_cookie(
        "selfpi_oauth_state",
        state,
        httponly=True,
        samesite=samesite,
        secure=secure,
        max_age=600,
        path="/",
    )


def clear_oauth_state_cookie(response: Response) -> None:
    secure, samesite = cookie_flags()
    response.delete_cookie(
        "selfpi_oauth_state",
        path="/",
        secure=secure,
        samesite=samesite,
    )


def sanitize_post_login_path(next_path: str | None) -> str:
    """Allow only same-origin relative paths (default /app)."""
    if not next_path:
        return "/app"
    path = next_path.strip().strip('"').strip("'")
    if not path.startswith("/") or path.startswith("//") or "\\" in path:
        return "/app"
    if path.startswith("/auth/"):
        return "/app"
    return path


def set_oauth_next_cookie(response: Response, next_path: str) -> None:
    secure, samesite = cookie_flags()
    response.set_cookie(
        "selfpi_oauth_next",
        sanitize_post_login_path(next_path),
        httponly=True,
        samesite=samesite,
        secure=secure,
        max_age=600,
        path="/",
    )


def clear_oauth_next_cookie(response: Response) -> None:
    secure, samesite = cookie_flags()
    response.delete_cookie(
        "selfpi_oauth_next",
        path="/",
        secure=secure,
        samesite=samesite,
    )


def session_user_public(session: dict[str, Any] | None) -> dict[str, Any] | None:
    if not session:
        return None
    return {
        "id": session.get("id"),
        "login": session.get("login"),
        "name": session.get("name"),
        "avatar_url": session.get("avatar_url"),
        "html_url": session.get("html_url"),
    }
