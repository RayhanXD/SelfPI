"""Python language module — lexing rules + surface→operation_id map.

Adding a language = adding a module under languages/. Don't scatter lang logic
through the pipeline (CLAUDE.md golden rule 5).
"""

from __future__ import annotations

from typing import Any

from detector.catalog import python_sdk_roots
from languages.python.imports import Binding, build_import_table
from languages.python.surfaces import SURFACE_TO_OPERATION
from languages.python.tokenizer import tokenize as _tokenize

LANGUAGE = "python"
name = "python"

OPERATION_TO_SURFACE: dict[str, tuple[str, ...]] = {
    op: path for path, op in SURFACE_TO_OPERATION.items()
}

# Default SDK root module names worth searching (from the API catalog).
SDK_ROOTS = python_sdk_roots()


def resolve_operation_id(path: list[str]) -> str | None:
    """Map a member-access path to a canonical operation_id."""
    return SURFACE_TO_OPERATION.get(tuple(path))


def tokenize(source: str) -> list[dict[str, Any]]:
    """Lex Python source into a token stream."""
    return _tokenize(source)


def import_table(tokens: list[dict[str, Any]]) -> dict[str, Binding]:
    return build_import_table(tokens)


def hints_for_operation(operation_id: str, *, extra: list[str] | None = None) -> list[str]:
    """Symbol hints for the prefilter recall net."""
    hints: list[str] = list(SDK_ROOTS)
    surface = OPERATION_TO_SURFACE.get(operation_id)
    if surface:
        hints.extend(surface)
    if extra:
        hints.extend(extra)
    # Dedupe, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for h in hints:
        if h and h not in seen:
            seen.add(h)
            out.append(h)
    return out
