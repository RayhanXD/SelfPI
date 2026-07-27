"""Public settings — no secrets; used by the Settings screen."""

from __future__ import annotations

from fastapi import APIRouter

from api.models import SettingsResponse
from db.settings import get_settings

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsResponse)
def get_public_settings() -> SettingsResponse:
    s = get_settings()
    configured = s.github_ready
    base = (s.github_default_base_branch or "").strip() or "(repo default)"
    return SettingsResponse(
        github_configured=configured,
        default_base_branch=base,
        repo_path_set=bool(s.repo_path),
        hint=(
            None
            if configured
            else (
                "Set GITHUB_APP_ID, GITHUB_APP_PRIVATE_KEY, and "
                "GITHUB_APP_INSTALLATION_ID in backend/.env — see README."
            )
        ),
    )
