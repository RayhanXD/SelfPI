"""Diff engine — compare two OpenAPI specs, emit BreakingChange[].

Pure function. No network / DB / LLM. Fixture-tested (M1).

Detects:
  - removed_field   — parameter or body property present in old, gone in new
  - renamed_param   — removed param paired with an added param (same `in` + type)
  - type_changed    — same name, schema type/format changed
  - value_deprecated — enum member present in old, absent in new
"""

from __future__ import annotations

from typing import Any

from diff.types import BreakingChange
from scanner.ir.enums import ChangeKind

_HTTP_METHODS = frozenset(
    {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
)


def detect_breaking_changes(
    old_spec: dict[str, Any], new_spec: dict[str, Any]
) -> list[BreakingChange]:
    """Detect removed_field | renamed_param | type_changed | value_deprecated."""
    old_ops = _index_operations(old_spec)
    new_ops = _index_operations(new_spec)

    changes: list[BreakingChange] = []
    for operation_id, old_op in old_ops.items():
        new_op = new_ops.get(operation_id)
        if new_op is None:
            # Entire operation removed — surface each old param/field as removed.
            changes.extend(_operation_fully_removed(operation_id, old_op))
            continue
        changes.extend(_diff_operation(operation_id, old_op, new_op))

    return _sorted(changes)


def _index_operations(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ops: dict[str, dict[str, Any]] = {}
    for _path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method not in _HTTP_METHODS or not isinstance(op, dict):
                continue
            op_id = op.get("operationId")
            if not op_id:
                continue
            ops[op_id] = op
    return ops


def _diff_operation(
    operation_id: str, old_op: dict[str, Any], new_op: dict[str, Any]
) -> list[BreakingChange]:
    changes: list[BreakingChange] = []

    old_params = _param_map(old_op)
    new_params = _param_map(new_op)

    removed_names = [n for n in old_params if n not in new_params]
    added_names = [n for n in new_params if n not in old_params]

    # Pair likely renames before treating leftovers as removals.
    renamed, still_removed, _still_added = _pair_renames(
        removed_names, added_names, old_params, new_params
    )
    for old_name, new_name in renamed:
        changes.append(
            BreakingChange(
                operation_id=operation_id,
                kind=ChangeKind.RENAMED_PARAM,
                detail={"param": old_name, "replacement": new_name},
            )
        )

    for name in still_removed:
        changes.append(
            BreakingChange(
                operation_id=operation_id,
                kind=ChangeKind.REMOVED_FIELD,
                detail={"field": name, "location": "parameter"},
            )
        )

    for name in old_params:
        if name not in new_params:
            continue
        changes.extend(
            _diff_schemas(
                operation_id,
                name,
                location="parameter",
                old_schema=_param_schema(old_params[name]),
                new_schema=_param_schema(new_params[name]),
            )
        )

    old_props = _body_properties(old_op)
    new_props = _body_properties(new_op)

    for name in old_props:
        if name not in new_props:
            changes.append(
                BreakingChange(
                    operation_id=operation_id,
                    kind=ChangeKind.REMOVED_FIELD,
                    detail={"field": name, "location": "body"},
                )
            )
            continue
        changes.extend(
            _diff_schemas(
                operation_id,
                name,
                location="body",
                old_schema=old_props[name],
                new_schema=new_props[name],
            )
        )

    return changes


def _operation_fully_removed(
    operation_id: str, old_op: dict[str, Any]
) -> list[BreakingChange]:
    changes: list[BreakingChange] = []
    for name in _param_map(old_op):
        changes.append(
            BreakingChange(
                operation_id=operation_id,
                kind=ChangeKind.REMOVED_FIELD,
                detail={"field": name, "location": "parameter"},
            )
        )
    for name in _body_properties(old_op):
        changes.append(
            BreakingChange(
                operation_id=operation_id,
                kind=ChangeKind.REMOVED_FIELD,
                detail={"field": name, "location": "body"},
            )
        )
    return changes


def _param_map(op: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for param in op.get("parameters") or []:
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if name:
            result[name] = param
    return result


def _param_schema(param: dict[str, Any]) -> dict[str, Any]:
    schema = param.get("schema")
    if isinstance(schema, dict):
        return schema
    return {}


def _body_properties(op: dict[str, Any]) -> dict[str, dict[str, Any]]:
    body = op.get("requestBody")
    if not isinstance(body, dict):
        return {}
    content = body.get("content") or {}
    # Prefer application/json; fall back to first media type.
    media = content.get("application/json")
    if media is None and content:
        media = next(iter(content.values()), None)
    if not isinstance(media, dict):
        return {}
    schema = media.get("schema") or {}
    if not isinstance(schema, dict):
        return {}
    props = schema.get("properties") or {}
    return {k: v for k, v in props.items() if isinstance(v, dict)}


def _pair_renames(
    removed: list[str],
    added: list[str],
    old_params: dict[str, dict[str, Any]],
    new_params: dict[str, dict[str, Any]],
) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """Greedy 1:1 rename pairing: same `in` + same schema type."""
    pairs: list[tuple[str, str]] = []
    remaining_removed = list(removed)
    remaining_added = list(added)

    for old_name in list(remaining_removed):
        old_p = old_params[old_name]
        old_in = old_p.get("in")
        old_type = _schema_type(_param_schema(old_p))
        match = None
        for new_name in remaining_added:
            new_p = new_params[new_name]
            if new_p.get("in") != old_in:
                continue
            if _schema_type(_param_schema(new_p)) != old_type:
                continue
            match = new_name
            break
        if match is not None:
            pairs.append((old_name, match))
            remaining_removed.remove(old_name)
            remaining_added.remove(match)

    return pairs, remaining_removed, remaining_added


def _diff_schemas(
    operation_id: str,
    name: str,
    *,
    location: str,
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
) -> list[BreakingChange]:
    changes: list[BreakingChange] = []
    key = "param" if location == "parameter" else "field"

    old_type = _schema_type(old_schema)
    new_type = _schema_type(new_schema)
    if old_type and new_type and old_type != new_type:
        changes.append(
            BreakingChange(
                operation_id=operation_id,
                kind=ChangeKind.TYPE_CHANGED,
                detail={
                    key: name,
                    "from_type": old_type,
                    "to_type": new_type,
                    "location": location,
                },
            )
        )

    old_enum = _enum_values(old_schema)
    new_enum = _enum_values(new_schema)
    if old_enum is not None and new_enum is not None:
        for value in old_enum:
            if value not in new_enum:
                changes.append(
                    BreakingChange(
                        operation_id=operation_id,
                        kind=ChangeKind.VALUE_DEPRECATED,
                        detail={
                            key: name,
                            "value": value,
                            "location": location,
                        },
                    )
                )

    return changes


def _schema_type(schema: dict[str, Any]) -> str | None:
    t = schema.get("type")
    if t is None:
        return None
    fmt = schema.get("format")
    if fmt:
        return f"{t}:{fmt}"
    return str(t)


def _enum_values(schema: dict[str, Any]) -> list[Any] | None:
    enum = schema.get("enum")
    if isinstance(enum, list):
        return list(enum)
    return None


def _sorted(changes: list[BreakingChange]) -> list[BreakingChange]:
    kind_order = {
        ChangeKind.RENAMED_PARAM: 0,
        ChangeKind.REMOVED_FIELD: 1,
        ChangeKind.TYPE_CHANGED: 2,
        ChangeKind.VALUE_DEPRECATED: 3,
    }
    return sorted(
        changes,
        key=lambda c: (
            c.operation_id,
            kind_order.get(c.kind, 99),
            str(c.detail),
        ),
    )
