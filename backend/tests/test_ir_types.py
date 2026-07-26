"""Smoke test — CallSite IR round-trips via pydantic."""

from scanner.ir.enums import ArgKind, SourceLayer, ValueKind
from scanner.ir.types import Arg, CallSite, ImportRef, Span


def test_call_site_round_trip():
    site = CallSite(
        file="billing.py",
        span=Span(start_line=12, end_line=12),
        language="python",
        receiver="stripe",
        path=["Charge", "create"],
        invoked=True,
        operation_id="createCharge",
        args=[
            Arg(
                name="source",
                value='"tok_123"',
                value_kind=ValueKind.LITERAL,
                kind=ArgKind.KEYWORD,
            )
        ],
        **{"import": ImportRef(module="stripe", symbol=None)},
        alias=None,
        in_comment=False,
        snippet='stripe.Charge.create(source="tok_123")',
        source_layer=SourceLayer.STRUCTURAL,
        confidence=0.92,
    )
    dumped = site.to_mongo()
    assert dumped["file"] == "billing.py"
    assert dumped["import"]["module"] == "stripe"
    assert dumped["source_layer"] == "structural"
    restored = CallSite.model_validate(dumped)
    assert restored.operation_id == "createCharge"
    assert restored.path == ["Charge", "create"]
