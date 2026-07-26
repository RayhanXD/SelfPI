"""Pre-filter — ripgrep candidate-file finder.

Deterministic recall net: never skip a file that mentions the changed symbol.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateMatch:
    file: str
    start_line: int
    end_line: int
    matched_text: str | None = None


def find_candidates(
    repo_path: str,
    hints: list[str],
    *,
    extensions: list[str] | None = None,
) -> list[CandidateMatch]:
    """Return candidate file paths (+ matched line ranges) for the given symbol/endpoint hints."""
    raise NotImplementedError("Prefilter — implement in M2")
