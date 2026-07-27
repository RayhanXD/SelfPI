"""Auto-detect third-party APIs from a connected local repo checkout.

Deterministic detection lives under languages/; this package resolves the
scan path and ensures matching watched APIs exist (Mongo side effects).
"""

from __future__ import annotations

from pathlib import Path

from detector.ensure import ensure_watched_apis
from detector.resolve import resolve_scan_path, stamp_repo_path
from languages.python.detect_apis import detect_apis as detect_python_apis

REPO_ROOT = Path(__file__).resolve().parents[2]


def detect_apis(repo_path: str | Path) -> list[str]:
    """Detect APIs used under repo_path. Pure over the filesystem; no DB/network."""
    return detect_python_apis(repo_path)


def detect_and_ensure(
    *,
    repo: str,
    repo_path: str | Path | None = None,
    connected: dict | None = None,
) -> dict:
    """Resolve a scan path, detect APIs, ensure live watched docs exist.

    Returns:
        {
          "detected_apis": ["stripe"],
          "ensured": ["stripe"],
          "repo_path": "/abs/path" | None,
        }
    """
    scan = resolve_scan_path(explicit=repo_path, connected=connected)
    detected = detect_apis(scan) if scan is not None else []
    stamp = stamp_repo_path(explicit=repo_path, connected=connected, scan=scan)
    ensured = ensure_watched_apis(
        detected,
        repo=repo,
        repo_path=stamp,
    )
    return {
        "detected_apis": detected,
        "ensured": ensured,
        "repo_path": str(scan) if scan is not None else None,
    }


__all__ = [
    "REPO_ROOT",
    "detect_apis",
    "detect_and_ensure",
    "ensure_watched_apis",
    "resolve_scan_path",
]
