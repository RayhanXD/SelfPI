"""Pydantic response/request models matching docs/API_CONTRACT.md."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from scanner.ir.enums import ApiStatus, ChangeKind, ChangeStatus, PrState, SourceLayer
from scanner.ir.types import CallSite


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class PrSummary(BaseModel):
    number: int
    url: str | None = None
    state: PrState
    tests_passing: bool | None = None
    opened_at: str | None = None


class ApiSummary(BaseModel):
    id: str
    name: str
    current_version: str | None = None
    status: ApiStatus
    languages: list[str] = Field(default_factory=list)
    last_checked: str | None = None
    open_change_count: int = 0
    repo: str | None = None
    spec_url: str | None = None
    mode: str | None = None  # "demo" | "live"
    # "detected" | "manual" | "seed" — how the watched API was created
    source: str | None = None


class SettingsResponse(BaseModel):
    github_configured: bool
    default_base_branch: str
    repo_path_set: bool
    hint: str | None = None
    connected_repo: str | None = None
    watch_interval_seconds: int = 300
    watch_enabled: bool = True
    oauth_configured: bool = False
    login_required: bool = False
    authenticated: bool = False
    user: AuthUser | None = None
    login_url: str | None = None
    # Install App onboarding (public)
    app_installed: bool = False
    install_url: str | None = None


class AuthUser(BaseModel):
    id: int | None = None
    login: str
    name: str | None = None
    avatar_url: str | None = None
    html_url: str | None = None


class MeResponse(BaseModel):
    authenticated: bool
    oauth_configured: bool
    login_required: bool
    user: AuthUser | None = None
    login_url: str | None = None
    app_installed: bool = False
    install_url: str | None = None


class HandoffRequest(BaseModel):
    handoff: str


class HandoffResponse(MeResponse):
    """Me payload plus a bearer token the SPA keeps when cross-site cookies are blocked."""

    session_token: str


class InstallationSyncResponse(BaseModel):
    app_installed: bool
    install_url: str | None = None
    installation_id: str | None = None


class ConnectedRepo(BaseModel):
    full_name: str
    owner: str
    name: str
    default_branch: str | None = None
    html_url: str | None = None
    private: bool | None = None
    repo_path: str | None = None
    connected_at: str | None = None
    # Populated by POST /repos/connect and POST /repos/connected/detect
    detected_apis: list[str] | None = None
    unwatchable: list[str] | None = None


class DetectApisResponse(BaseModel):
    detected_apis: list[str] = Field(default_factory=list)
    ensured: list[str] = Field(default_factory=list)
    # Detected catalog ids that have no public OpenAPI URL yet.
    unwatchable: list[str] = Field(default_factory=list)
    repo_path: str | None = None
    full_name: str | None = None


class InstallationRepo(BaseModel):
    full_name: str
    owner: str
    name: str
    private: bool = False
    default_branch: str = "main"
    html_url: str | None = None
    connected: bool = False


class ListInstallationReposResponse(BaseModel):
    items: list[InstallationRepo]
    connected_repo: str | None = None


class ConnectRepoRequest(BaseModel):
    full_name: str
    repo_path: str | None = None


class CreateApiRequest(BaseModel):
    id: str
    name: str
    spec_url: str
    repo: str
    languages: list[str] = Field(default_factory=lambda: ["python"])


class CheckApiResponse(BaseModel):
    checked: bool
    new_version: str | None = None
    changes_detected: int = 0
    # True when this poll stored the first (or re-)baseline and skipped diffing.
    baseline: bool = False
    # True when the fetched OpenAPI fingerprint matches the latest stored version.
    unchanged: bool = False


class SpecDiff(BaseModel):
    operation_id: str
    removed: list[str] = Field(default_factory=list)
    added: list[str] = Field(default_factory=list)
    raw: str | None = None


class ChangeSummary(BaseModel):
    id: str
    api_id: str
    operation_id: str
    kind: ChangeKind
    detail: dict[str, Any] = Field(default_factory=dict)
    call_site_count: int = 0
    status: ChangeStatus
    pr: PrSummary | None = None
    detected_at: str | None = None


class ChangeListResponse(BaseModel):
    items: list[ChangeSummary]
    next_cursor: str | None = None


class ChangeDetail(BaseModel):
    id: str
    api_id: str
    operation_id: str
    kind: ChangeKind
    detail: dict[str, Any] = Field(default_factory=dict)
    from_version: str | None = None
    to_version: str | None = None
    status: ChangeStatus
    repo: str | None = None
    spec_diff: SpecDiff | None = None
    call_sites: list[CallSite] = Field(default_factory=list)
    pr: PrSummary | None = None
    detected_at: str | None = None


class RescanResponse(BaseModel):
    call_site_count: int
    status: ChangeStatus


class SpecVersionSummary(BaseModel):
    version: str
    fetched_at: str | None = None


class PushSpecRequest(BaseModel):
    version: str
    spec: dict[str, Any]


class PushSpecResponse(BaseModel):
    version: str
    changes_detected: int = 0
