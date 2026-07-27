"""Resolve which local directory to scan for API usage."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_scan_path(
    *,
    explicit: str | Path | None = None,
    connected: dict[str, Any] | None = None,
) -> Path | None:
    """Pick an existing local directory to scan.

    Prod-style: only explicit or the connected workspace ``repo_path``.
    No silent fallback to demo-consumer / global REPO_PATH (that caused
    connecting C.Y.R.U.S. to detect Stripe from the demo tree).
    """
    candidates: list[str | Path] = []
    if explicit is not None and str(explicit).strip():
        candidates.append(explicit)
    if connected and connected.get("repo_path"):
        candidates.append(connected["repo_path"])

    seen: set[Path] = set()
    for raw in candidates:
        path = Path(raw).expanduser().resolve()
        if path in seen:
            continue
        seen.add(path)
        if path.is_dir():
            return path
    return None


def stamp_repo_path(
    *,
    explicit: str | Path | None = None,
    connected: dict[str, Any] | None = None,
    scan: Path | None = None,
) -> str | None:
    """Path to write onto watched APIs — prefer the workspace binding."""
    if explicit is not None and str(explicit).strip():
        return str(Path(explicit).expanduser())
    if connected and connected.get("repo_path"):
        return str(connected["repo_path"])
    if scan is not None:
        return str(scan)
    return None
