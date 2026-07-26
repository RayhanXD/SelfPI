"""IR normalizer — token stream + import pre-pass → CallSite[].

Deterministic. Pure. No network / DB / LLM.
"""

from __future__ import annotations

from typing import Any

from languages import get_language
from languages.python.calls import extract_call_sites
from languages.python.imports import Binding
from scanner.ir.types import CallSite


def normalize(
    tokens: list[dict],
    *,
    file: str,
    language: str,
    imports: dict | None = None,
    source: str | None = None,
) -> list[CallSite]:
    """Convert a token stream into CallSite records.

    Populate: receiver, path, invoked, args, location, in_comment, operation_id.
    """
    if language != "python":
        raise NotImplementedError(f"IR normalizer for language={language!r} not implemented")

    lang = get_language("python")
    table: dict[str, Binding]
    if imports is None:
        table = lang.import_table(tokens)
    else:
        table = imports  # type: ignore[assignment]

    return extract_call_sites(
        tokens,
        file=file,
        language=language,
        imports=table,
        source=source,
    )


def normalize_source(source: str, *, file: str, language: str = "python") -> list[CallSite]:
    """Convenience: tokenize + import pre-pass + normalize in one call."""
    lang = get_language(language)
    tokens = lang.tokenize(source)
    return normalize(tokens, file=file, language=language, source=source)
