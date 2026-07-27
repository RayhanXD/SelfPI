"""BSON-safe coercion for OpenAPI specs with oversized integers / dates."""

from __future__ import annotations

from datetime import date

from bson import BSON

from db.bson_safe import bson_safe


def test_bson_safe_converts_oversized_ints():
    raw = {
        "minimum": -(1 << 63) - 1000,
        "maximum": (1 << 63) + 1000,
        "ok": 42,
        "nested": [{"x": (1 << 63)}],
    }
    safe = bson_safe(raw)
    assert safe["ok"] == 42
    assert isinstance(safe["minimum"], str)
    assert isinstance(safe["maximum"], str)
    assert isinstance(safe["nested"][0]["x"], str)
    BSON.encode({"spec": safe})  # must not raise


def test_bson_safe_converts_dates():
    safe = bson_safe({"released": date(2024, 10, 1), "nested": [date(2020, 1, 1)]})
    assert safe["released"] == "2024-10-01"
    assert safe["nested"][0] == "2020-01-01"
    BSON.encode({"spec": safe})


def test_openai_seed_bounds_are_storable():
    # Values seen in openai-openapi CreateChatCompletionRequest.seed
    raw = {
        "components": {
            "schemas": {
                "seed": {
                    "minimum": -9223372036854776000,
                    "maximum": 9223372036854776000,
                    "since": date(2024, 10, 1),
                }
            }
        }
    }
    safe = bson_safe(raw)
    BSON.encode({"spec": safe})
