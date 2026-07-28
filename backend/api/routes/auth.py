"""GitHub OAuth — Login with GitHub + Install App callback."""

from __future__ import annotations

import logging
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from api.auth.installation import (
    install_url,
    installation_status,
    resolve_installation_id,
    sync_installation_id,
)
from api.auth.oauth import authorize_url, exchange_code, fetch_github_user
from api.auth.session import (
    clear_oauth_next_cookie,
    clear_oauth_state_cookie,
    clear_session_cookie,
    consume_handoff_token,
    create_handoff_token,
    dump_session,
    read_session,
    sanitize_post_login_path,
    session_user_public,
    set_oauth_next_cookie,
    set_oauth_state_cookie,
    set_session_cookie,
)
from api.models import AuthUser, HandoffRequest, HandoffResponse, InstallationSyncResponse, MeResponse
from db.settings import get_settings

logger = logging.getLogger("selfpi.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/github/login")
def github_login(next: str | None = None) -> RedirectResponse:
    """Start Login with GitHub. Optional `next` is where the SPA lands after auth."""
    s = get_settings()
    dest = sanitize_post_login_path(next)
    if not s.oauth_ready:
        return RedirectResponse(
            f"{s.frontend_url.rstrip('/')}/auth/callback?"
            f"{urlencode({'auth': 'error', 'reason': 'oauth_not_configured', 'next': dest})}",
            status_code=302,
        )
    state = secrets.token_urlsafe(24)
    url = authorize_url(state=state)
    response = RedirectResponse(url, status_code=302)
    set_oauth_state_cookie(response, state)
    set_oauth_next_cookie(response, dest)
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
    next_path = sanitize_post_login_path(request.cookies.get("selfpi_oauth_next"))

    def fail(reason: str) -> RedirectResponse:
        response = RedirectResponse(
            f"{frontend}/auth/callback?"
            f"{urlencode({'auth': 'error', 'reason': reason, 'next': next_path})}",
            status_code=302,
        )
        clear_oauth_state_cookie(response)
        clear_oauth_next_cookie(response)
        return response

    if error:
        return fail(error)
    if not code or not state:
        return fail("missing_code")

    expected = request.cookies.get("selfpi_oauth_state")
    if expected:
        expected = expected.strip().strip('"').strip("'")
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
    try:
        sync_installation_id(session)
    except Exception as exc:
        logger.warning("installation sync on login failed: %s", exc)

    handoff = create_handoff_token(session)
    response = RedirectResponse(
        f"{frontend}/auth/callback?"
        f"{urlencode({'auth': 'ok', 'next': next_path, 'handoff': handoff})}",
        status_code=302,
    )
    set_session_cookie(response, session)
    clear_oauth_state_cookie(response)
    clear_oauth_next_cookie(response)
    return response


@router.get("/github/install")
def github_install(request: Request) -> RedirectResponse:
    """Redirect to GitHub's Install App page (requires App credentials)."""
    s = get_settings()
    frontend = s.frontend_url.rstrip("/")
    url = install_url()
    if not url:
        return RedirectResponse(
            f"{frontend}/app/settings?install=error&reason=install_url_unavailable",
            status_code=302,
        )
    # Prefer logged-in users; still allow anonymous click-through to GitHub.
    _ = read_session(request)
    return RedirectResponse(url, status_code=302)


@router.get("/github/installed")
def github_installed(
    request: Request,
    installation_id: str | None = None,
    setup_action: str | None = None,
) -> RedirectResponse:
    """GitHub App Setup URL target after Install / Update.

    Configure on the App: Setup URL → `{API}/auth/github/installed`
    GitHub appends `?installation_id=…&setup_action=install|update`.
    """
    s = get_settings()
    frontend = s.frontend_url.rstrip("/")
    session = read_session(request)

    if not session:
        # Bounce through login, then land on settings.
        return RedirectResponse(
            f"{frontend}/login?next=/app/settings&reason=install_needs_login",
            status_code=302,
        )

    if installation_id:
        sync_installation_id(session, installation_id=installation_id)
    else:
        try:
            sync_installation_id(session)
        except Exception as exc:
            logger.warning("post-install sync failed: %s", exc)

    params = {"installed": "1"}
    if setup_action:
        params["setup_action"] = setup_action
    if not resolve_installation_id(session):
        params = {"installed": "0", "reason": "no_installation"}

    response = RedirectResponse(
        f"{frontend}/app/settings?{urlencode(params)}",
        status_code=302,
    )
    set_session_cookie(response, session)
    return response


@router.post("/github/sync-installation", response_model=InstallationSyncResponse)
def sync_installation(request: Request) -> JSONResponse:
    """Re-discover this user's App installation and refresh the session cookie."""
    s = get_settings()
    session = read_session(request)
    if not session or not session_user_public(session):
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "login_required",
                    "message": "Log in with GitHub first.",
                }
            },
        )
    if not s.github_app_credentials_ready:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "github_not_configured",
                    "message": "GitHub App credentials are not configured on the server.",
                }
            },
        )

    try:
        sync_installation_id(session)
    except Exception as exc:
        logger.exception("sync-installation failed: %s", exc)
        return JSONResponse(
            status_code=502,
            content={
                "error": {
                    "code": "github_sync_failed",
                    "message": str(exc),
                }
            },
        )

    status = installation_status(session)
    body = InstallationSyncResponse(
        app_installed=bool(status["app_installed"]),
        install_url=status.get("install_url"),
        installation_id=status.get("installation_id"),
    )
    response = JSONResponse(body.model_dump())
    set_session_cookie(response, session)
    return response


@router.get("/me", response_model=MeResponse)
def me(request: Request) -> MeResponse:
    s = get_settings()
    session = read_session(request)
    user = session_user_public(session)
    status = installation_status(session)
    return MeResponse(
        authenticated=bool(user),
        oauth_configured=s.oauth_ready,
        login_required=s.login_required,
        user=AuthUser(**user) if user else None,
        login_url="/auth/github/login" if s.oauth_ready else None,
        app_installed=bool(status["app_installed"]),
        install_url=status.get("install_url"),
    )


@router.post("/handoff", response_model=HandoffResponse)
def complete_handoff(body: HandoffRequest) -> JSONResponse:
    """Exchange the one-time OAuth handoff for a session cookie + bearer token.

    Cross-origin SPAs (Vercel → CloudFront) often cannot read the Set-Cookie from
    the GitHub redirect; the SPA posts the handoff and keeps `session_token`.
    """
    s = get_settings()
    session = consume_handoff_token(body.handoff)
    user = session_user_public(session)
    if not session or not user:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "handoff_invalid",
                    "message": "Sign-in expired. Try Continue with GitHub again.",
                }
            },
        )

    status = installation_status(session)
    payload = HandoffResponse(
        authenticated=True,
        oauth_configured=s.oauth_ready,
        login_required=s.login_required,
        user=AuthUser(**user),
        login_url="/auth/github/login" if s.oauth_ready else None,
        app_installed=bool(status["app_installed"]),
        install_url=status.get("install_url"),
        session_token=dump_session(session),
    )
    response = JSONResponse(payload.model_dump())
    set_session_cookie(response, session)
    return response


@router.post("/logout")
def logout() -> JSONResponse:
    response = JSONResponse({"logged_out": True})
    clear_session_cookie(response)
    return response
