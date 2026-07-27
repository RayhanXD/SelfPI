"""Connected GitHub repo — list installation repos + connect/disconnect."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth.deps import require_login
from api.models import (
    ConnectRepoRequest,
    ConnectedRepo,
    InstallationRepo,
    ListInstallationReposResponse,
)
from db.repos import connect_repo, connected_summary, disconnect_repo, get_connected_repo
from db.settings import get_settings
from patcher.github import GitHubAppClient

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("/connected", response_model=ConnectedRepo | None)
def get_connected(_user: dict = Depends(require_login)) -> ConnectedRepo | None:
    summary = connected_summary()
    if not summary:
        return None
    return ConnectedRepo(**summary)


@router.get("", response_model=ListInstallationReposResponse)
def list_accessible_repos(_user: dict = Depends(require_login)) -> ListInstallationReposResponse:
    """Repos the GitHub App installation can access (installation token)."""
    s = get_settings()
    if not s.github_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "github_not_configured",
                    "message": (
                        "GitHub App not configured. Set GITHUB_APP_ID, "
                        "GITHUB_APP_PRIVATE_KEY, and GITHUB_APP_INSTALLATION_ID."
                    ),
                }
            },
        )
    client = GitHubAppClient()
    try:
        raw = client.list_installation_repos()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": {"code": "github_list_failed", "message": str(exc)}},
        ) from exc

    connected = get_connected_repo()
    connected_name = (connected or {}).get("full_name")
    items = [
        InstallationRepo(
            full_name=r["full_name"],
            owner=r["owner"],
            name=r["name"],
            private=bool(r.get("private")),
            default_branch=r.get("default_branch") or "main",
            html_url=r.get("html_url"),
            connected=r["full_name"] == connected_name,
        )
        for r in raw
    ]
    return ListInstallationReposResponse(items=items, connected_repo=connected_name)


@router.post("/connect", response_model=ConnectedRepo)
def connect(body: ConnectRepoRequest, _user: dict = Depends(require_login)) -> ConnectedRepo:
    """Persist the connected repo and stamp it onto watched APIs."""
    s = get_settings()
    full_name = body.full_name.strip()
    meta: dict = {}

    if s.github_ready:
        try:
            client = GitHubAppClient()
            for item in client.list_installation_repos():
                if item["full_name"] == full_name:
                    meta = item
                    break
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail={"error": {"code": "github_list_failed", "message": str(exc)}},
            ) from exc
        if not meta:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "repo_not_accessible",
                        "message": (
                            f"Repository '{full_name}' is not accessible to this "
                            "GitHub App installation. Install the App on that repo "
                            "or pick one from GET /repos."
                        ),
                    }
                },
            )

    try:
        doc = connect_repo(
            full_name=full_name,
            owner=meta.get("owner"),
            name=meta.get("name"),
            default_branch=meta.get("default_branch"),
            html_url=meta.get("html_url"),
            private=meta.get("private"),
            repo_path=body.repo_path if body.repo_path is not None else s.repo_path,
            propagate_to_apis=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "invalid_repo", "message": str(exc)}},
        ) from exc

    return ConnectedRepo(**connected_summary(doc))  # type: ignore[arg-type]


@router.delete("/connected", response_model=dict)
def disconnect(_user: dict = Depends(require_login)) -> dict:
    deleted = disconnect_repo(clear_api_repos=False)
    return {"disconnected": deleted}
