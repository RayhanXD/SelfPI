"""Spec watcher — polls upstream OpenAPI specs and stores new versions.

Out: new spec_versions doc when the spec changes.
"""

from __future__ import annotations

from typing import Any


async def poll_api(api_id: str) -> dict[str, Any]:
    """Fetch the current spec for an API; store a new version if it changed.

    Returns: { checked: bool, new_version: str | None, changes_detected: int }
    """
    raise NotImplementedError("Watcher — implement after M0")
