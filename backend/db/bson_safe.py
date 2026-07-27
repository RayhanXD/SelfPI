"""Make nested values safe for BSON / MongoDB inserts.

OpenAPI YAML/JSON can include:
- integers outside signed int64 (OpenAI `seed` min/max) → OverflowError
- `datetime.date` from YAML timestamps → InvalidDocument

Coerce those (and a few other non-BSON types) before insert.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

# BSON int64 bounds
_INT64_MIN = -(1 << 63)
_INT64_MAX = (1 << 63) - 1


def bson_safe(value: Any) -> Any:
    """Recursively coerce values PyMongo cannot encode."""
    if value is None or isinstance(value, (bool, str, float, bytes)):
        return value
    if isinstance(value, int):
        if value < _INT64_MIN or value > _INT64_MAX:
            return str(value)
        return value
    if isinstance(value, datetime):
        return value  # supported by BSON
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        # Prefer int when exact and in range; else string (avoids float drift).
        if value == value.to_integral_value():
            as_int = int(value)
            if _INT64_MIN <= as_int <= _INT64_MAX:
                return as_int
            return str(as_int)
        return str(value)
    if isinstance(value, dict):
        return {str(k): bson_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [bson_safe(v) for v in value]
    if isinstance(value, set):
        return [bson_safe(v) for v in value]
    # Last resort — string form beats insert failure
    return str(value)
