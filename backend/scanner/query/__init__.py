"""Query / matcher — DSL compiled from a BreakingChange, run over CallSite[].

Deterministic. Pure.
"""

from __future__ import annotations

from typing import Any

from diff.types import BreakingChange
from scanner.ir.types import CallSite


def compile_query(change: BreakingChange) -> dict[str, Any]:
    """Compile a BreakingChange into a matcher query against the IR."""
    raise NotImplementedError("Query compiler — implement in M2")


def match(call_sites: list[CallSite], query: dict[str, Any]) -> list[CallSite]:
    """Return CallSites that satisfy the compiled query."""
    raise NotImplementedError("Query matcher — implement in M2")
