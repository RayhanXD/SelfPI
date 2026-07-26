"""IR normalizer — token stream + import pre-pass → CallSite[].

Deterministic. Pure. No network / DB / LLM.
"""

from __future__ import annotations

from scanner.ir.types import CallSite


def normalize(
    tokens: list[dict],
    *,
    file: str,
    language: str,
    imports: dict | None = None,
) -> list[CallSite]:
    """Convert a token stream into CallSite records.

    Populate incrementally: start with receiver, path, invoked, args[].name,
    location, in_comment for Python (design doc §6).
    """
    raise NotImplementedError("IR normalizer — implement in M2")
