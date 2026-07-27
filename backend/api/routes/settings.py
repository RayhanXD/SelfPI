"""Public settings — no secrets; used by the Settings screen."""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.auth.installation import installation_status
from api.auth.session import read_session, session_user_public
from api.models import AuthUser, SettingsResponse
from db.repos import get_connected_repo
from db.settings import get_settings

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
def get_public_settings(request: Request) -> SettingsResponse:
    s = get_settings()
    session = read_session(request)
    status = installation_status(session)
    # "Configured" = server has App credentials (Install + list/PR can work).
    configured = s.github_app_credentials_ready
    base = (s.github_default_base_branch or "").strip() or "(repo default)"
    connected = get_connected_repo()
    connected_name = (connected or {}).get("full_name")
    repo_path_set = bool(s.repo_path) or bool((connected or {}).get("repo_path"))
    user = session_user_public(session)
    app_installed = bool(status["app_installed"])

    hint = None
    if not configured:
        hint = (
            "Set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY in backend/.env — "
            "users install the App from Settings (no INSTALLATION_ID required)."
        )
    elif s.login_required and not user:
        hint = "Log in with GitHub to install the App and connect a repository."
    elif user and not app_installed:
        hint = "Install SelfPI on GitHub, then connect a repository."
    elif not s.oauth_ready:
        hint = (
            "Optional: set GITHUB_CLIENT_ID + GITHUB_CLIENT_SECRET for "
            "Login with GitHub (production auth)."
        )

    return SettingsResponse(
        github_configured=configured,
        default_base_branch=base,
        repo_path_set=repo_path_set,
        connected_repo=connected_name,
        watch_interval_seconds=int(s.watch_interval_seconds or 300),
        watch_enabled=bool(s.watch_enabled),
        oauth_configured=s.oauth_ready,
        login_required=s.login_required,
        authenticated=bool(user),
        user=AuthUser(**user) if user else None,
        login_url="/auth/github/login" if s.oauth_ready else None,
        app_installed=app_installed,
        install_url=status.get("install_url"),
        hint=hint,
    )
