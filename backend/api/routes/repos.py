"""Connected GitHub repo — list installation repos + connect/disconnect."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth.deps import require_login
from api.auth.installation import resolve_installation_id, sync_installation_id
from api.auth.session import read_session, set_session_cookie
from api.models import (
    ConnectRepoRequest,
    ConnectedRepo,
    DetectApisResponse,
    InstallationRepo,
    ListInstallationReposResponse,
)
from db.repos import connect_repo, connected_summary, disconnect_repo, get_connected_repo
from db.settings import get_settings
from detector import detect_and_ensure
from patcher.github import GitHubAppClient
from starlette.responses import JSONResponse, Response

router = APIRouter(prefix="/repos", tags=["repos"])


def _client_for_request(request: Request) -> tuple[GitHubAppClient, dict | None]:
    """Build a GitHubAppClient using session / connected / env installation id.

    May mutate the session when discovering an installation via the user token.
    Returns (client, updated_session_or_None).
    """
    s = get_settings()
    if not s.github_app_credentials_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "github_not_configured",
                    "message": (
                        "GitHub App not configured. Set GITHUB_APP_ID and "
                        "GITHUB_APP_PRIVATE_KEY."
                    ),
                }
            },
        )

    session = read_session(request)
    updated = session
    iid = resolve_installation_id(session)
    if not iid and session and session.get("access_token"):
        try:
            sync_installation_id(session)
            iid = resolve_installation_id(session)
            updated = session
        except Exception:
            pass

    if not iid:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "app_not_installed",
                    "message": (
                        "SelfPI is not installed on any of your GitHub accounts yet. "
                        "Open Settings → Install SelfPI on GitHub, then try again."
                    ),
                }
            },
        )

    return GitHubAppClient(installation_id=iid), updated


def _maybe_refresh_session(response: Response, session: dict | None) -> None:
    if session is not None:
        set_session_cookie(response, session)


@router.get("/connected", response_model=ConnectedRepo | None)
def get_connected(_user: dict = Depends(require_login)) -> ConnectedRepo | None:
    summary = connected_summary()
    if not summary:
        return None
    return ConnectedRepo(**summary)


@router.get("", response_model=ListInstallationReposResponse)
def list_accessible_repos(
    request: Request, _user: dict = Depends(require_login)
) -> Response:
    """Repos the GitHub App installation can access (installation token)."""
    client, session = _client_for_request(request)
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
    body = ListInstallationReposResponse(items=items, connected_repo=connected_name)
    response = JSONResponse(body.model_dump())
    _maybe_refresh_session(response, session)
    return response


@router.post("/connect", response_model=ConnectedRepo)
def connect(
    body: ConnectRepoRequest,
    request: Request,
    _user: dict = Depends(require_login),
) -> Response:
    """Persist the connected repo and stamp it onto watched APIs."""
    s = get_settings()
    full_name = body.full_name.strip()
    meta: dict = {}
    session: dict | None = None
    installation_id = resolve_installation_id(read_session(request))

    if s.github_app_credentials_ready:
        client, session = _client_for_request(request)
        installation_id = client.installation_id
        try:
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
            installation_id=str(installation_id) if installation_id else None,
            propagate_to_apis=True,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "invalid_repo", "message": str(exc)}},
        ) from exc

    detection = detect_and_ensure(
        repo=doc["full_name"],
        repo_path=doc.get("repo_path"),
        connected=doc,
    )
    summary = connected_summary(doc) or {}
    summary["detected_apis"] = detection["detected_apis"]
    response = JSONResponse(ConnectedRepo(**summary).model_dump())
    _maybe_refresh_session(response, session)
    return response


@router.post("/connected/detect", response_model=DetectApisResponse)
def detect_connected_apis(_user: dict = Depends(require_login)) -> DetectApisResponse:
    """Re-scan the connected repo checkout and ensure live watched APIs."""
    doc = get_connected_repo()
    if not doc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "no_connected_repo",
                    "message": "Connect a repository first (POST /repos/connect).",
                }
            },
        )
    detection = detect_and_ensure(
        repo=doc["full_name"],
        repo_path=doc.get("repo_path"),
        connected=doc,
    )
    return DetectApisResponse(
        detected_apis=detection["detected_apis"],
        ensured=detection["ensured"],
        repo_path=detection["repo_path"],
        full_name=doc.get("full_name"),
    )


@router.delete("/connected", response_model=dict)
def disconnect(_user: dict = Depends(require_login)) -> dict:
    deleted = disconnect_repo(clear_api_repos=False)
    return {"disconnected": deleted}
