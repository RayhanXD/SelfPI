"""Diff engine fixture tests — old/new/expected triples per change kind.

Recall/precision: exact match against expected.json (design doc §11).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from diff.engine import detect_breaking_changes

FIXTURES_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "diff"
KINDS = ("renamed_param", "removed_field", "type_changed", "value_deprecated")


def _load(path: Path) -> object:
    return json.loads(path.read_text())


@pytest.mark.parametrize("kind", KINDS)
def test_diff_fixture(kind: str) -> None:
    case_dir = FIXTURES_ROOT / kind
    old_spec = _load(case_dir / "old.json")
    new_spec = _load(case_dir / "new.json")
    expected = _load(case_dir / "expected.json")

    assert isinstance(old_spec, dict)
    assert isinstance(new_spec, dict)
    assert isinstance(expected, list)

    actual = detect_breaking_changes(old_spec, new_spec)
    actual_dicts = [c.model_dump(mode="json") for c in actual]
    assert actual_dicts == expected


def test_identical_specs_yield_no_changes() -> None:
    case_dir = FIXTURES_ROOT / "renamed_param"
    old_spec = _load(case_dir / "old.json")
    assert isinstance(old_spec, dict)
    assert detect_breaking_changes(old_spec, old_spec) == []


def test_no_false_rename_when_types_differ() -> None:
    """Removed + added with different types → removed_field, not rename."""
    old = {
        "openapi": "3.1.0",
        "paths": {
            "/x": {
                "post": {
                    "operationId": "op",
                    "parameters": [
                        {"name": "a", "in": "query", "schema": {"type": "string"}}
                    ],
                }
            }
        },
    }
    new = {
        "openapi": "3.1.0",
        "paths": {
            "/x": {
                "post": {
                    "operationId": "op",
                    "parameters": [
                        {"name": "b", "in": "query", "schema": {"type": "integer"}}
                    ],
                }
            }
        },
    }
    changes = detect_breaking_changes(old, new)
    kinds = [c.kind.value for c in changes]
    assert "renamed_param" not in kinds
    assert any(c.kind.value == "removed_field" and c.detail["field"] == "a" for c in changes)
