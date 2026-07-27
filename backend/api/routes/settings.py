"""Public settings — no secrets; used by the Settings screen."""

from __future__ import annotations

from fastapi import APIRouter

from api.models import SettingsResponse
from db.repos import get_connected_repo
from db.settings import get_settings

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
def get_public_settings() -> SettingsResponse:
    s = get_settings()
    configured = s.github_ready
    base = (s.github_default_base_branch or "").strip() or "(repo default)"
    connected = get_connected_repo()
    connected_name = (connected or {}).get("full_name")
    repo_path_set = bool(s.repo_path) or bool((connected or {}).get("repo_path"))
    return SettingsResponse(
        github_configured=configured,
        default_base_branch=base,
        repo_path_set=repo_path_set,
        connected_repo=connected_name,
        watch_interval_seconds=int(s.watch_interval_seconds or 300),
        watch_enabled=bool(s.watch_enabled),
        hint=(
            None
            if configured
            else (
                "Set GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, and "
                "GITHUB_APP_INSTALLATION_ID in backend/.env — see README."
            )
        ),
    )
