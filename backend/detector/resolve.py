"""Resolve which local directory to scan for API usage."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from db.settings import get_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_CONSUMER = REPO_ROOT / "demo-consumer"


def resolve_scan_path(
    *,
    explicit: str | Path | None = None,
    connected: dict[str, Any] | None = None,
) -> Path | None:
    """Pick the first existing directory among configured paths:

    1. explicit path (e.g. connect request repo_path)
    2. connected repo's repo_path
    3. settings.repo_path / REPO_PATH

    If none of those are configured, fall back to local ``demo-consumer/``
    when present. A configured path that does not exist does **not** fall
    through to demo-consumer (avoids stamping the wrong tree).
    """
    configured: list[str | Path] = []
    if explicit is not None and str(explicit).strip():
        configured.append(explicit)
    if connected and connected.get("repo_path"):
        configured.append(connected["repo_path"])
    settings = get_settings()
    if settings.repo_path:
        configured.append(settings.repo_path)

    seen: set[Path] = set()
    for raw in configured:
        path = Path(raw).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        if path.is_dir():
            return path

    if not configured and DEMO_CONSUMER.is_dir():
        return DEMO_CONSUMER.resolve()
    return None


def stamp_repo_path(
    *,
    explicit: str | Path | None = None,
    connected: dict[str, Any] | None = None,
    scan: Path | None = None,
) -> str | None:
    """Path to write onto watched APIs — prefer the workspace binding, not a fallback scan."""
    if explicit is not None and str(explicit).strip():
        return str(Path(explicit).expanduser())
    if connected and connected.get("repo_path"):
        return str(connected["repo_path"])
    if scan is not None:
        return str(scan)
    return None
