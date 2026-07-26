"""Diff package."""

from diff.engine import detect_breaking_changes
from diff.types import BreakingChange

__all__ = ["BreakingChange", "detect_breaking_changes"]
