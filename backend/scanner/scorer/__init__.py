"""Scorer — multi-signal confidence over matched CallSite records.

Deterministic. Pure. Signals: exact token hit +, correct import +, arg match +, in-comment −.
"""

from __future__ import annotations

from scanner.ir.enums import SourceLayer
from scanner.ir.types import CallSite


def score(call_sites: list[CallSite], *, query: dict | None = None) -> list[CallSite]:
    """Attach confidence + source_layer to each matched CallSite."""
    arg_names = set((query or {}).get("arg_names") or [])
    scored: list[CallSite] = []

    for site in call_sites:
        confidence = 0.55
        layer = SourceLayer.STRUCTURAL

        if site.in_comment:
            confidence -= 0.45
            layer = SourceLayer.GREP
        else:
            confidence += 0.15

        if site.import_ is not None:
            confidence += 0.15

        if site.operation_id:
            confidence += 0.10

        if arg_names:
            site_args = {a.name for a in site.args if a.name}
            if site_args & arg_names:
                confidence += 0.10

        # Dynamic args are slightly less certain (adjudicator territory)
        if any(a.value_kind and a.value_kind.value == "dynamic" for a in site.args):
            confidence -= 0.05

        if site.in_test_file:
            confidence -= 0.05

        confidence = max(0.0, min(1.0, confidence))

        scored.append(
            site.model_copy(update={"confidence": confidence, "source_layer": layer})
        )

    return scored
