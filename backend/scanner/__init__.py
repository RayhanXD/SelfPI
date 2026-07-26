"""Scanner pipeline orchestration — prefilter → tokenize → IR → query → score."""

from __future__ import annotations

from typing import TYPE_CHECKING

from scanner.ir.types import CallSite

if TYPE_CHECKING:
    from diff.types import BreakingChange


def scan(
    repo_path: str,
    change: BreakingChange,
    *,
    language: str = "python",
) -> list[CallSite]:
    """Run the deterministic scanner pipeline for one BreakingChange against a repo.

    Adjudication (LLM) is M3 — this returns scored candidates, including gray-zone.
    """
    from pathlib import Path

    from languages import get_language
    from scanner.ir.normalizer import normalize
    from scanner.prefilter import find_candidates
    from scanner.query import compile_query, match
    from scanner.scorer import score
    from scanner.tokenizer import tokenize

    lang = get_language(language)
    detail = change.detail or {}
    extra_hints: list[str] = []
    for key in ("param", "field", "replacement"):
        if detail.get(key):
            extra_hints.append(str(detail[key]))

    hints = lang.hints_for_operation(change.operation_id, extra=extra_hints)
    candidates = find_candidates(repo_path, hints)
    files = sorted({c.file for c in candidates})

    # Recall net: if prefilter found nothing, still scan all language files.
    root = Path(repo_path)
    if not files:
        ext = ".py" if language == "python" else ".*"
        files = sorted(
            str(p.relative_to(root))
            for p in root.rglob(f"*{ext}")
            if p.is_file() and not any(part.startswith(".") for part in p.parts)
        )

    all_sites: list[CallSite] = []
    for rel in files:
        path = root / rel
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        tokens = tokenize(source, lang)
        all_sites.extend(
            normalize(tokens, file=rel, language=language, source=source)
        )

    query = compile_query(change)
    matched = match(all_sites, query)
    return score(matched, query=query)
