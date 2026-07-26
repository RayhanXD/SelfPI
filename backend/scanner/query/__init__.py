"""Query / matcher — DSL compiled from a BreakingChange, run over CallSite[].

Deterministic. Pure.
"""

from __future__ import annotations

from typing import Any

from diff.types import BreakingChange
from scanner.ir.enums import ChangeKind
from scanner.ir.types import CallSite


def compile_query(change: BreakingChange) -> dict[str, Any]:
    """Compile a BreakingChange into a matcher query against the IR."""
    arg_names: list[str] = []
    literal_value: str | None = None

    detail = change.detail or {}
    if change.kind == ChangeKind.RENAMED_PARAM:
        if detail.get("param"):
            arg_names.append(str(detail["param"]))
    elif change.kind == ChangeKind.REMOVED_FIELD:
        field = detail.get("field") or detail.get("param")
        if field:
            arg_names.append(str(field))
    elif change.kind == ChangeKind.TYPE_CHANGED:
        field = detail.get("param") or detail.get("field")
        if field:
            arg_names.append(str(field))
    elif change.kind == ChangeKind.VALUE_DEPRECATED:
        field = detail.get("param") or detail.get("field")
        if field:
            arg_names.append(str(field))
        if "value" in detail:
            literal_value = str(detail["value"])

    return {
        "operation_id": change.operation_id,
        "kind": change.kind.value,
        "arg_names": arg_names,
        "literal_value": literal_value,
    }


def match(call_sites: list[CallSite], query: dict[str, Any]) -> list[CallSite]:
    """Return CallSites that satisfy the compiled query.

    Recall-first: match operation_id; when arg_names are set, require at least
    one matching arg name. Literal value filters are applied when present
    (value_deprecated) but only drop sites that have a conflicting literal —
    dynamic args still match (routed to adjudicator later).
    """
    op_id = query.get("operation_id")
    arg_names = set(query.get("arg_names") or [])
    literal_value = query.get("literal_value")

    matched: list[CallSite] = []
    for site in call_sites:
        if op_id and site.operation_id != op_id:
            continue

        if arg_names:
            site_arg_names = {a.name for a in site.args if a.name}
            if site_arg_names.isdisjoint(arg_names):
                continue

        if literal_value is not None:
            # Keep if any matching arg is dynamic OR literal equals the deprecated value
            relevant = [a for a in site.args if a.name in arg_names] if arg_names else site.args
            if relevant:
                keep = False
                for a in relevant:
                    if a.value_kind and a.value_kind.value == "dynamic":
                        keep = True
                        break
                    if a.value is not None and _strip_quotes(a.value) == literal_value:
                        keep = True
                        break
                if not keep:
                    continue

        matched.append(site)

    return matched


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value
