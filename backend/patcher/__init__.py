"""Patcher — LLM agent that writes a fix and opens a GitHub PR.

Isolates LLM + GitHub/network I/O from the deterministic core.
"""

from __future__ import annotations

from typing import Any

from diff.types import BreakingChange
from scanner.ir.types import CallSite


def generate_and_open_pr(
    call_sites: list[CallSite],
    change: BreakingChange,
    *,
    repo: str,
) -> dict[str, Any]:
    """Generate a fix for confirmed call sites and open a PR. Returns PR metadata."""
    raise NotImplementedError("Patcher — implement in M3")
