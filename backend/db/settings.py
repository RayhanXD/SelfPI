"""Application settings — loaded from environment / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "selfpi"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    # development | production — production enables Secure cookies + SameSite=None
    env: str = "development"

    # LLM (adjudicator + PR copy) — optional; heuristic client used when unset
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # GitHub App (patcher opens PRs) — optional; dry-run local apply when unset
    github_app_id: str | None = None
    github_app_private_key: str | None = None
    # Optional env fallback for single-tenant / local demo. Public installs
    # discover installation_id via Login + Install App (stored on session / connected repo).
    github_app_installation_id: str | None = None
    # Optional slug for install URL; when empty, fetched from GET /app via App JWT.
    github_app_slug: str | None = None
    github_default_base_branch: str = ""  # empty = use each repo's GitHub default_branch

    # GitHub App user OAuth ("Login with GitHub")
    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_oauth_redirect_uri: str = "http://localhost:8000/auth/github/callback"
    frontend_url: str = "http://localhost:5173"
    session_secret: str = "dev-change-me-selfpi-session"
    # When true and OAuth is configured, /repos/* requires a logged-in session
    auth_required: bool = True

    # Local path to the connected repo checkout (scanner target)
    repo_path: str | None = None

    # Background watcher — polls live watched APIs on an interval
    watch_interval_seconds: int = 300
    watch_enabled: bool = True
    # Show stripe-demo on the dashboard (local harness only). Prod default: off.
    include_demo_apis: bool = False

    @property
    def is_production(self) -> bool:
        """True when ENV=production/prod, or FRONTEND_URL is https (hosted UI)."""
        if self.env.strip().lower() in ("production", "prod"):
            return True
        return self.frontend_url.strip().lower().startswith("https://")

    @property
    def github_app_credentials_ready(self) -> bool:
        """App ID + private key — enough to mint JWTs and serve Install App."""
        return bool(self.github_app_id and self.github_app_private_key)

    @property
    def github_ready(self) -> bool:
        """Env has full App config including a default installation id."""
        return bool(
            self.github_app_credentials_ready and self.github_app_installation_id
        )

    @property
    def oauth_ready(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret)

    @property
    def login_required(self) -> bool:
        """Gate connect-repo behind Login with GitHub when OAuth is configured."""
        return bool(self.auth_required and self.oauth_ready)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def github_ready() -> bool:
    """True when real PRs can be opened (credentials + some installation id)."""
    s = get_settings()
    if not s.github_app_credentials_ready:
        return False
    if s.github_app_installation_id:
        return True
    from db.repos import get_connected_repo

    doc = get_connected_repo()
    return bool(doc and doc.get("installation_id"))


def pr_pipeline_flags() -> tuple[bool, bool]:
    """Return (open_pr, dry_run_pr) for bump/check routes.

    When the App is configured: open real PRs.
    Otherwise: skip PR opening entirely (no fake PR embeds).
    """
    if github_ready():
        return True, False
    return False, True
