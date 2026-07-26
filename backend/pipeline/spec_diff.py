"""Build the API-contract `spec_diff` embed from a BreakingChange."""

from __future__ import annotations

from typing import Any

from diff.types import BreakingChange
from scanner.ir.enums import ChangeKind


def build_spec_diff(change: BreakingChange) -> dict[str, Any]:
    detail = change.detail or {}
    removed: list[str] = []
    added: list[str] = []
    raw_lines: list[str] = []

    if change.kind == ChangeKind.RENAMED_PARAM:
        param = str(detail.get("param", ""))
        replacement = str(detail.get("replacement", ""))
        if param:
            removed.append(param)
            raw_lines.append(f"- {param}")
        if replacement:
            added.append(replacement)
            raw_lines.append(f"+ {replacement}")
    elif change.kind == ChangeKind.REMOVED_FIELD:
        field = str(detail.get("field") or detail.get("param") or "")
        if field:
            removed.append(field)
            raw_lines.append(f"- {field}")
    elif change.kind == ChangeKind.TYPE_CHANGED:
        name = str(detail.get("param") or detail.get("field") or "")
        from_t = detail.get("from_type")
        to_t = detail.get("to_type")
        raw_lines.append(f"- {name}: {from_t}")
        raw_lines.append(f"+ {name}: {to_t}")
    elif change.kind == ChangeKind.VALUE_DEPRECATED:
        name = str(detail.get("param") or detail.get("field") or "")
        value = detail.get("value")
        removed.append(str(value))
        raw_lines.append(f"- {name} enum value {value!r} deprecated/removed")

    return {
        "operation_id": change.operation_id,
        "removed": removed,
        "added": added,
        "raw": "\n".join(raw_lines) if raw_lines else None,
    }
