"""Auth dependencies — require Login with GitHub when OAuth is configured."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request

from api.auth.session import read_session, session_user_public
from db.settings import get_settings


def current_session(request: Request) -> dict[str, Any] | None:
    return read_session(request)


def current_user(request: Request) -> dict[str, Any] | None:
    return session_user_public(read_session(request))


def require_login(request: Request) -> dict[str, Any]:
    """When OAuth is configured + auth_required, demand a session user."""
    s = get_settings()
    session = read_session(request)
    user = session_user_public(session)
    if s.login_required and not user:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "login_required",
                    "message": "Log in with GitHub to connect a repository.",
                }
            },
        )
    return user or {}
