"""Breaking-change types produced by the diff engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from scanner.ir.enums import ChangeKind


class BreakingChange(BaseModel):
    operation_id: str
    kind: ChangeKind
    detail: dict[str, Any] = Field(default_factory=dict)
