"""GitHub OAuth — Login with GitHub."""

from __future__ import annotations

import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from api.auth.oauth import authorize_url, exchange_code, fetch_github_user
from api.auth.session import (
    clear_session_cookie,
    read_session,
    session_user_public,
    set_session_cookie,
)
from api.models import AuthUser, MeResponse
from db.settings import get_settings

logger = logging.getLogger("selfpi.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/login")
def github_login() -> RedirectResponse:
    s = get_settings()
    if not s.oauth_ready:
        return RedirectResponse(
            f"{s.frontend_url.rstrip('/')}/auth/callback?auth=error&reason=oauth_not_configured",
            status_code=302,
        )
    state = secrets.token_urlsafe(24)
    url = authorize_url(state=state)
    response = RedirectResponse(url, status_code=302)
    # Short-lived state cookie for CSRF
    response.set_cookie(
        "selfpi_oauth_state",
        state,
        httponly=True,
        samesite="lax",
        max_age=600,
        path="/",
    )
    return response


@router.get("/github/callback")
def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    s = get_settings()
    frontend = s.frontend_url.rstrip("/")

    def fail(reason: str) -> RedirectResponse:
        return RedirectResponse(
            f"{frontend}/auth/callback?{urlencode({'auth': 'error', 'reason': reason})}",
            status_code=302,
        )

    if error:
        return fail(error)
    if not code or not state:
        return fail("missing_code")

    expected = request.cookies.get("selfpi_oauth_state")
    if not expected or expected != state:
        return fail("bad_state")

    try:
        token = exchange_code(code)
        gh_user = fetch_github_user(token)
    except Exception as exc:
        logger.exception("oauth callback failed: %s", exc)
        return fail("token_exchange_failed")

    session = {
        "id": gh_user.get("id"),
        "login": gh_user.get("login"),
        "name": gh_user.get("name"),
        "avatar_url": gh_user.get("avatar_url"),
        "html_url": gh_user.get("html_url"),
        "access_token": token,
    }
    response = RedirectResponse(f"{frontend}/auth/callback?auth=ok", status_code=302)
    set_session_cookie(response, session)
    response.delete_cookie("selfpi_oauth_state", path="/")
    return response


@router.get("/me", response_model=MeResponse)
def me(request: Request) -> MeResponse:
    s = get_settings()
    user = session_user_public(read_session(request))
    return MeResponse(
        authenticated=bool(user),
        oauth_configured=s.oauth_ready,
        login_required=s.login_required,
        user=AuthUser(**user) if user else None,
        login_url="/auth/github/login" if s.oauth_ready else None,
    )


@router.post("/logout")
def logout() -> JSONResponse:
    response = JSONResponse({"logged_out": True})
    clear_session_cookie(response)
    return response
