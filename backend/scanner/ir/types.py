"""Call-Site IR — language-agnostic record shape (design doc §6).

All languages normalize to this contract. Schema changes are a design signal.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from scanner.ir.enums import ArgKind, SourceLayer, ValueKind


class Span(BaseModel):
    start_line: int
    end_line: int
    start_col: int | None = None
    end_col: int | None = None


class Arg(BaseModel):
    name: str | None = None
    value: str | None = None
    value_kind: ValueKind | None = None
    kind: ArgKind
    pos: int | None = None


class ImportRef(BaseModel):
    module: str
    symbol: str | None = None


class CallSite(BaseModel):
    """Normalized call-site record produced by the scanner pipeline."""

    id: str | None = None
    file: str
    span: Span
    language: str

    receiver: str | None = None
    path: list[str] = Field(default_factory=list)
    invoked: bool = False
    args: list[Arg] = Field(default_factory=list)

    operation_id: str | None = None
    import_: ImportRef | None = Field(default=None, alias="import")
    alias: str | None = None

    in_comment: bool = False
    in_string: bool = False
    in_test_file: bool = False

    snippet: str | None = None
    source_layer: SourceLayer | None = None
    confidence: float | None = None

    model_config = {"populate_by_name": True}

    def to_mongo(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
