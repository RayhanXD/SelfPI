"""Smoke test — Python language module surface→operation_id map."""

from languages.python import resolve_operation_id


def test_resolve_create_charge():
    assert resolve_operation_id(["Charge", "create"]) == "createCharge"


def test_resolve_unknown():
    assert resolve_operation_id(["Unknown", "method"]) is None
