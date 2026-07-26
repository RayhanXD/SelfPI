"""Scanner fixture tests — golden CallSite IR + full pipeline recall."""

from __future__ import annotations

import json
from pathlib import Path

from diff.types import BreakingChange
from languages.python import tokenize
from languages.python.imports import build_import_table
from scanner import scan
from scanner.ir.enums import ChangeKind
from scanner.ir.normalizer import normalize_source
from scanner.prefilter import find_candidates
from scanner.query import compile_query, match
from scanner.scorer import score

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPO = REPO_ROOT / "fixtures" / "sample_repo"
GOLDEN = REPO_ROOT / "fixtures" / "scanner" / "python" / "billing_expected.json"


def test_tokenize_marks_comments():
    tokens = tokenize("x = 1  # stripe.Charge.create()\n")
    comments = [t for t in tokens if t["type"] == "COMMENT"]
    assert len(comments) == 1
    assert comments[0]["in_comment"] is True


def test_import_table_alias():
    tokens = tokenize("import stripe as s\n")
    table = build_import_table(tokens)
    assert "s" in table
    assert table["s"].module == "stripe"
    assert table["s"].alias == "s"


def test_normalize_billing_golden_recall():
    source = (SAMPLE_REPO / "billing.py").read_text()
    expected = json.loads(GOLDEN.read_text())["expected_call_sites"]

    sites = normalize_source(source, file="billing.py", language="python")

    # Comment trap must not produce a call site
    assert all(not s.in_comment for s in sites)
    assert not any("tok_comment" in (s.snippet or "") for s in sites)

    assert len(sites) == len(expected), f"recall fail: got {len(sites)} expected {len(expected)}"

    for site, exp in zip(sites, expected, strict=True):
        assert site.span.start_line == exp["span"]["start_line"]
        assert site.receiver == exp["receiver"]
        assert site.path == exp["path"]
        assert site.invoked is exp["invoked"]
        assert site.operation_id == exp["operation_id"]
        assert site.in_comment is exp["in_comment"]
        assert len(site.args) >= 1
        assert site.args[0].name == exp["args"][0]["name"]
        assert site.args[0].value_kind.value == exp["args"][0]["value_kind"]
        assert site.args[0].kind.value == exp["args"][0]["kind"]


def test_prefilter_finds_billing():
    matches = find_candidates(str(SAMPLE_REPO), ["stripe", "Charge", "create", "source"])
    files = {m.file for m in matches}
    assert "billing.py" in files
    assert any(m.start_line <= 4 <= m.end_line for m in matches if m.file == "billing.py")


def test_query_and_score_renamed_source():
    source = (SAMPLE_REPO / "billing.py").read_text()
    sites = normalize_source(source, file="billing.py")
    change = BreakingChange(
        operation_id="createCharge",
        kind=ChangeKind.RENAMED_PARAM,
        detail={"param": "source", "replacement": "payment_method"},
    )
    query = compile_query(change)
    matched = match(sites, query)
    scored = score(matched, query=query)

    assert len(scored) == 2
    assert all(s.operation_id == "createCharge" for s in scored)
    assert all(s.confidence is not None and s.confidence >= 0.6 for s in scored)
    assert all(s.source_layer is not None for s in scored)


def test_scan_pipeline_end_to_end():
    change = BreakingChange(
        operation_id="createCharge",
        kind=ChangeKind.RENAMED_PARAM,
        detail={"param": "source", "replacement": "payment_method"},
    )
    results = scan(str(SAMPLE_REPO), change, language="python")
    assert len(results) == 2
    lines = sorted(s.span.start_line for s in results)
    assert lines == [4, 10]
    assert all(s.receiver == "stripe" for s in results)
    assert all(any(a.name == "source" for a in s.args) for s in results)
