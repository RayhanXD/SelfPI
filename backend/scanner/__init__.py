"""Scanner pipeline orchestration — prefilter → tokenize → IR → query → score → adjudicate."""

from __future__ import annotations

from diff.types import BreakingChange
from scanner.ir.types import CallSite


def scan(
    repo_path: str,
    change: BreakingChange,
    *,
    language: str = "python",
) -> list[CallSite]:
    """Run the full scanner pipeline for one BreakingChange against a repo."""
    raise NotImplementedError("Scanner pipeline — wire in M2/M3")
