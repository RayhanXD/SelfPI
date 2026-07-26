"""Pre-filter — ripgrep candidate-file finder.

Deterministic recall net: never skip a file that mentions the changed symbol.
Handoff: file paths + matched line ranges + small context window.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CandidateMatch:
    file: str
    start_line: int
    end_line: int
    matched_text: str | None = None


DEFAULT_EXTENSIONS = [".py"]
CONTEXT_LINES = 2


def find_candidates(
    repo_path: str,
    hints: list[str],
    *,
    extensions: list[str] | None = None,
    context_lines: int = CONTEXT_LINES,
) -> list[CandidateMatch]:
    """Return candidate file paths (+ matched line ranges) for the given hints."""
    if not hints:
        return []
    exts = extensions or DEFAULT_EXTENSIONS
    root = Path(repo_path)
    if not root.is_dir():
        raise FileNotFoundError(f"Repo path not found: {repo_path}")

    rg = _resolve_rg()
    if rg:
        matches = _rg_search(rg, root, hints, exts)
    else:
        matches = _python_search(root, hints, exts)

    return _with_context(matches, context_lines)


def _resolve_rg() -> str | None:
    env = os.environ.get("RG_PATH")
    if env and Path(env).is_file():
        return env
    found = shutil.which("rg")
    if found:
        return found
    cursor_rg = (
        "/Applications/Cursor.app/Contents/Resources/app/node_modules/@vscode/ripgrep/bin/rg"
    )
    if Path(cursor_rg).is_file():
        return cursor_rg
    return None


def _rg_search(rg: str, root: Path, hints: list[str], exts: list[str]) -> list[CandidateMatch]:
    pattern = "|".join(re.escape(h) for h in hints)
    cmd = [rg, "--json", "-n", "--no-heading", pattern]
    for ext in exts:
        glob = f"*{ext}" if ext.startswith(".") else f"*.{ext}"
        cmd.extend(["-g", glob])
    cmd.append(str(root))

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    # rg exit 1 = no matches; 0 = matches; 2 = error
    if proc.returncode not in (0, 1):
        return _python_search(root, hints, exts)

    matches: list[CandidateMatch] = []
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "match":
            continue
        data = event.get("data") or {}
        path_data = data.get("path") or {}
        line_data = data.get("line_number")
        text_data = (data.get("lines") or {}).get("text")
        path = path_data.get("text")
        if not path or line_data is None:
            continue
        rel = str(Path(path).resolve().relative_to(root.resolve()))
        text = text_data.rstrip("\n") if isinstance(text_data, str) else None
        matches.append(
            CandidateMatch(file=rel, start_line=int(line_data), end_line=int(line_data), matched_text=text)
        )
    return matches


def _python_search(root: Path, hints: list[str], exts: list[str]) -> list[CandidateMatch]:
    """Fallback recall net when ripgrep is unavailable."""
    pattern = re.compile("|".join(re.escape(h) for h in hints))
    matches: list[CandidateMatch] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in exts and not any(str(path).endswith(e) for e in exts):
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(path.relative_to(root))
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                matches.append(
                    CandidateMatch(
                        file=rel, start_line=lineno, end_line=lineno, matched_text=line.strip()
                    )
                )
    return matches


def _with_context(matches: list[CandidateMatch], context_lines: int) -> list[CandidateMatch]:
    if context_lines <= 0:
        return matches
    return [
        CandidateMatch(
            file=m.file,
            start_line=max(1, m.start_line - context_lines),
            end_line=m.end_line + context_lines,
            matched_text=m.matched_text,
        )
        for m in matches
    ]
