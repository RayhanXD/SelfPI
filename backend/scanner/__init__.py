"""Scanner pipeline orchestration — prefilter → tokenize → IR → query → score → adjudicate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scanner.ir.types import CallSite

if TYPE_CHECKING:
    from diff.types import BreakingChange


def scan(
    repo_path: str,
    change: BreakingChange,
    *,
    language: str = "python",
) -> list[CallSite]:
    """Run the full scanner pipeline for one BreakingChange against a repo."""
    raise NotImplementedError("Scanner pipeline — wire in M2/M3")
