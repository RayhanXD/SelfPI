"""Tokenizer — per-language lexer over candidate source files.

Deterministic. Pure. Language quirks live in languages/<lang>/.
"""

from __future__ import annotations

from typing import Any, Protocol


class LanguageModule(Protocol):
    name: str

    def tokenize(self, source: str) -> list[dict[str, Any]]: ...


def tokenize(source: str, language: LanguageModule) -> list[dict[str, Any]]:
    """Lex source into a token stream via the language module."""
    raise NotImplementedError("Tokenizer — implement in M2")
