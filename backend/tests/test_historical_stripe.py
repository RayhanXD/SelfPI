"""M6 — historical Stripe rename fixture: diff + scan recall."""

from __future__ import annotations

import json
from pathlib import Path

from diff.engine import detect_breaking_changes
from diff.types import BreakingChange
from scanner import scan
from scanner.ir.enums import ChangeKind

REPO_ROOT = Path(__file__).resolve().parents[2]
HIST = REPO_ROOT / "fixtures" / "historical" / "stripe_source_to_payment_method"
CONSUMER = REPO_ROOT / "fixtures" / "historical" / "consumer"


def _load(name: str):
    return json.loads((HIST / name).read_text())


def test_historical_diff_detects_source_rename():
    old = _load("old.json")
    new = _load("new.json")
    expected = _load("expected.json")
    changes = detect_breaking_changes(old, new)
    assert len(changes) == 1
    assert changes[0].operation_id == expected[0]["operation_id"]
    assert changes[0].kind.value == expected[0]["kind"]
    assert changes[0].detail == expected[0]["detail"]


def test_historical_consumer_scan_recall():
    change = BreakingChange(
        operation_id="createCharge",
        kind=ChangeKind.RENAMED_PARAM,
        detail={"param": "source", "replacement": "payment_method"},
    )
    sites = scan(str(CONSUMER), change, language="python")
    assert len(sites) == 2
    lines = {s.span.start_line for s in sites}
    assert lines == {4, 10}
    assert all(s.operation_id == "createCharge" for s in sites)
