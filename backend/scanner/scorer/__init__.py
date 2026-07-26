"""Scorer — multi-signal confidence over matched CallSite records.

Deterministic. Pure. Signals: exact token hit +, correct import +, arg match +, in-comment −.
"""

from __future__ import annotations

from scanner.ir.types import CallSite


def score(call_sites: list[CallSite]) -> list[CallSite]:
    """Attach confidence + source_layer to each matched CallSite."""
    raise NotImplementedError("Scorer — implement in M2")
