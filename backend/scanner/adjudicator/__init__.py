"""Adjudicator — bounded LLM review of gray-zone CallSite records.

Only confirms/rejects candidates the deterministic layers already produced.
Never scans the repo on its own.
"""

from __future__ import annotations

from scanner.ir.types import CallSite


def adjudicate(candidates: list[CallSite], *, change_context: dict | None = None) -> list[CallSite]:
    """Confirm or reject gray-zone records. Returns confirmed CallSites only."""
    raise NotImplementedError("Adjudicator — implement in M3")
