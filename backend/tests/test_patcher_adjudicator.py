"""Outcome tests for adjudicator + patcher (design doc §11 / ENGINEERING_PLAN §4).

Patched sample repo must compile; mechanical rename is verified on disk.
GitHub App calls are unit-tested with a fake client (no network).
"""

from __future__ import annotations

import py_compile
import shutil
from pathlib import Path

from diff.types import BreakingChange
from llm.client import HeuristicClient
from patcher import apply_patches_locally, generate_and_open_pr
from patcher.patches import build_edits
from scanner import scan
from scanner.adjudicator import adjudicate
from scanner.ir.enums import ChangeKind, SourceLayer
from scanner.ir.types import Arg, CallSite, Span
from scanner.ir.enums import ArgKind, ValueKind

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPO = REPO_ROOT / "fixtures" / "sample_repo"


def _rename_change() -> BreakingChange:
    return BreakingChange(
        operation_id="createCharge",
        kind=ChangeKind.RENAMED_PARAM,
        detail={"param": "source", "replacement": "payment_method"},
    )


def test_adjudicator_auto_includes_high_confidence():
    high = CallSite(
        id="high1",
        file="billing.py",
        span=Span(start_line=4, end_line=4),
        language="python",
        receiver="stripe",
        path=["Charge", "create"],
        invoked=True,
        operation_id="createCharge",
        args=[Arg(name="source", value='"tok"', value_kind=ValueKind.LITERAL, kind=ArgKind.KEYWORD)],
        in_comment=False,
        confidence=0.92,
        source_layer=SourceLayer.STRUCTURAL,
    )
    confirmed = adjudicate([high], llm=HeuristicClient())
    assert len(confirmed) == 1
    assert confirmed[0].id == "high1"


def test_adjudicator_rejects_comment_via_heuristic():
    low = CallSite(
        id="cmt1",
        file="billing.py",
        span=Span(start_line=7, end_line=7),
        language="python",
        receiver="stripe",
        path=["Charge", "create"],
        invoked=True,
        operation_id="createCharge",
        args=[Arg(name="source", kind=ArgKind.KEYWORD)],
        in_comment=True,
        confidence=0.2,
        source_layer=SourceLayer.GREP,
    )
    confirmed = adjudicate([low], change_context={"kind": "renamed_param"}, llm=HeuristicClient())
    assert confirmed == []


def test_outcome_patched_sample_repo_compiles(tmp_path: Path):
    """ENGINEERING_PLAN §4: patched sample repo compiles + change applied."""
    work = tmp_path / "sample_repo"
    shutil.copytree(SAMPLE_REPO, work)

    change = _rename_change()
    sites = scan(str(work), change, language="python")
    confirmed = adjudicate(sites, change_context=change.model_dump(mode="json"), llm=HeuristicClient())
    assert len(confirmed) == 2

    edited = apply_patches_locally(work, confirmed, change)
    assert "billing.py" in edited

    billing = (work / "billing.py").read_text()
    assert 'payment_method="tok_123"' in billing
    assert "payment_method=customer_card" in billing
    # Real call sites rewritten; comment trap may still mention source=
    call_lines = [
        ln
        for ln in billing.splitlines()
        if "Charge.create" in ln and not ln.strip().startswith("#")
    ]
    assert call_lines
    assert all("source=" not in ln for ln in call_lines)

    py_compile.compile(str(work / "billing.py"), doraise=True)


def test_generate_and_open_pr_dry_run(tmp_path: Path):
    work = tmp_path / "sample_repo"
    shutil.copytree(SAMPLE_REPO, work)
    change = _rename_change()
    sites = scan(str(work), change)
    confirmed = adjudicate(sites, llm=HeuristicClient())

    class FakeGitHub:
        configured = True

        def create_pull_request(self, **kwargs):
            raise AssertionError("dry_run should not call GitHub")

    result = generate_and_open_pr(
        confirmed,
        change,
        repo="myorg/billing-app",
        repo_path=work,
        dry_run=True,
        llm=HeuristicClient(),
        github=FakeGitHub(),  # type: ignore[arg-type]
    )
    assert result["dry_run"] is True
    assert "billing.py" in result["edited_files"]
    assert 'payment_method="tok_123"' in (work / "billing.py").read_text()


def test_generate_and_open_pr_uses_github_client(tmp_path: Path):
    work = tmp_path / "sample_repo"
    shutil.copytree(SAMPLE_REPO, work)
    change = _rename_change()
    sites = scan(str(work), change)
    confirmed = adjudicate(sites, llm=HeuristicClient())
    edits = build_edits(work, confirmed, change)

    class FakeGitHub:
        configured = True
        last = None

        def create_pull_request(self, **kwargs):
            self.last = kwargs
            return {
                "number": 42,
                "url": "https://github.com/myorg/billing-app/pull/42",
                "state": "open",
                "tests_passing": None,
                "opened_at": "2026-07-01T00:10:00Z",
            }

    gh = FakeGitHub()
    result = generate_and_open_pr(
        confirmed,
        change,
        repo="myorg/billing-app",
        repo_path=work,
        dry_run=False,
        llm=HeuristicClient(),
        github=gh,  # type: ignore[arg-type]
    )
    assert result["number"] == 42
    assert result["dry_run"] is False
    assert gh.last is not None
    assert "billing.py" in gh.last["files"]
    assert edits[0].new_content == gh.last["files"]["billing.py"]
