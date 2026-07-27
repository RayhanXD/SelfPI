"""Auto-detect third-party APIs from a connected repo checkout.

Deterministic detection lives under languages/; this package resolves the
scan path (cloning from GitHub when needed) and ensures watched APIs exist.
"""

from __future__ import annotations

import logging
from pathlib import Path

from detector.catalog import get_entry
from detector.checkout import REPO_ROOT, ensure_github_checkout
from detector.ensure import ensure_watched_apis
from detector.resolve import resolve_scan_path, stamp_repo_path
from languages.python.detect_apis import detect_apis as detect_python_apis

logger = logging.getLogger("selfpi.detector")


def detect_apis(repo_path: str | Path) -> list[str]:
    """Detect APIs used under repo_path. Pure over the filesystem; no DB/network."""
    return detect_python_apis(repo_path)


def detect_and_ensure(
    *,
    repo: str,
    repo_path: str | Path | None = None,
    connected: dict | None = None,
    installation_id: str | None = None,
    clone: bool = True,
) -> dict:
    """Resolve a scan path, detect APIs, ensure live watched docs exist.

    If no local path exists for ``repo``, shallow-clones it via the GitHub App
    into ``.cache/checkouts/`` (prod path — same as hosted).
    """
    scan = resolve_scan_path(explicit=repo_path, connected=connected)
    clone_error: str | None = None

    if scan is None and clone and repo and "/" in repo:
        iid = installation_id or (connected or {}).get("installation_id")
        branch = (connected or {}).get("default_branch")
        try:
            scan = ensure_github_checkout(
                repo,
                installation_id=str(iid) if iid else None,
                branch=branch,
            )
        except Exception as exc:
            clone_error = str(exc)
            logger.warning("checkout failed for %s: %s", repo, exc)

    detected = detect_apis(scan) if scan is not None else []
    stamp = stamp_repo_path(explicit=repo_path, connected=connected, scan=scan)
    # Prefer the resolved scan path (clone) as the durable workspace path.
    if scan is not None:
        stamp = str(scan)

    ensured = ensure_watched_apis(
        detected,
        repo=repo,
        repo_path=stamp,
    )

    unwatchable = [
        api_id
        for api_id in detected
        if (entry := get_entry(api_id)) is not None and not entry.watchable
    ]
    return {
        "detected_apis": detected,
        "ensured": ensured,
        "unwatchable": unwatchable,
        "repo_path": str(scan) if scan is not None else None,
        "clone_error": clone_error,
    }


__all__ = [
    "REPO_ROOT",
    "detect_apis",
    "detect_and_ensure",
    "ensure_watched_apis",
    "resolve_scan_path",
]
