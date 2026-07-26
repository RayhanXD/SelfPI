"""Diff engine — compare two OpenAPI specs, emit BreakingChange[].

Pure function. No network / DB / LLM. Fixture-tested (M1).
"""

from __future__ import annotations

from typing import Any

from diff.types import BreakingChange


def detect_breaking_changes(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> list[BreakingChange]:
    """Detect removed_field | renamed_param | type_changed | value_deprecated."""
    raise NotImplementedError("Diff engine — implement in M1")
