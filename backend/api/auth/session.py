"""Signed cookie session for GitHub OAuth users."""

from __future__ import annotations

import json
from typing import Any

from itsdangerous import BadSignature, URLSafeSerializer
from starlette.requests import Request
from starlette.responses import Response

from db.settings import get_settings

COOKIE_NAME = "selfpi_session"


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


def set_session_cookie(response: Response, data: dict[str, Any]) -> None:
    response.set_cookie(
        COOKIE_NAME,
        dump_session(data),
        httponly=True,
        samesite="lax",
        secure=False,  # localhost; set True behind HTTPS in prod
        max_age=60 * 60 * 24 * 14,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


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
