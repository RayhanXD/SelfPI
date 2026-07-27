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

    # LLM (adjudicator + PR copy) — optional; heuristic client used when unset
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # GitHub App (patcher opens PRs) — optional; dry-run local apply when unset
    github_app_id: str | None = None
    github_app_private_key: str | None = None
    github_app_installation_id: str | None = None
    github_default_base_branch: str = ""  # empty = use each repo's GitHub default_branch

    # Local path to the connected repo checkout (scanner target)
    repo_path: str | None = None

    # Background watcher — polls live watched APIs on an interval
    watch_interval_seconds: int = 300
    watch_enabled: bool = True

    @property
    def github_ready(self) -> bool:
        return bool(
            self.github_app_id
            and self.github_app_private_key
            and self.github_app_installation_id
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def github_ready() -> bool:
    """True when GitHub App credentials are present (real PRs can be opened)."""
    return get_settings().github_ready


def pr_pipeline_flags() -> tuple[bool, bool]:
    """Return (open_pr, dry_run_pr) for bump/check routes.

    When the App is configured: open real PRs.
    Otherwise: skip PR opening entirely (no fake PR embeds).
    """
    if github_ready():
        return True, False
    return False, True
