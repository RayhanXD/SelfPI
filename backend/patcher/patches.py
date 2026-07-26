"""Mechanical patches for known BreakingChange kinds (deterministic core of patcher)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from diff.types import BreakingChange
from scanner.ir.enums import ChangeKind
from scanner.ir.types import CallSite


@dataclass(frozen=True)
class FileEdit:
    path: str
    old_content: str
    new_content: str


def build_edits(
    repo_path: str | Path,
    call_sites: list[CallSite],
    change: BreakingChange,
) -> list[FileEdit]:
    """Produce file-level edits for confirmed call sites."""
    root = Path(repo_path)
    by_file: dict[str, list[CallSite]] = {}
    for site in call_sites:
        by_file.setdefault(site.file, []).append(site)

    edits: list[FileEdit] = []
    for rel, sites in sorted(by_file.items()):
        path = root / rel
        original = path.read_text(encoding="utf-8")
        updated = original
        # Apply from bottom of file upward so line numbers stay valid
        for site in sorted(sites, key=lambda s: s.span.start_line, reverse=True):
            updated = _apply_site(updated, site, change)
        if updated != original:
            edits.append(FileEdit(path=rel, old_content=original, new_content=updated))
    return edits


def apply_edits(repo_path: str | Path, edits: list[FileEdit]) -> list[str]:
    """Write edits to disk. Returns list of relative paths written."""
    root = Path(repo_path)
    written: list[str] = []
    for edit in edits:
        (root / edit.path).write_text(edit.new_content, encoding="utf-8")
        written.append(edit.path)
    return written


def _apply_site(source: str, site: CallSite, change: BreakingChange) -> str:
    lines = source.splitlines(keepends=True)
    idx = site.span.start_line - 1
    if idx < 0 or idx >= len(lines):
        return source

    line = lines[idx]
    new_line = _rewrite_line(line, change)
    if new_line == line:
        return source
    lines[idx] = new_line
    return "".join(lines)


def _rewrite_line(line: str, change: BreakingChange) -> str:
    detail = change.detail or {}
    if change.kind == ChangeKind.RENAMED_PARAM:
        old = str(detail.get("param", ""))
        new = str(detail.get("replacement", ""))
        if not old or not new:
            return line
        # keyword arg: old= → new=
        pattern = rf"(\b){re.escape(old)}(\s*=)"
        return re.sub(pattern, rf"\1{new}\2", line)

    if change.kind == ChangeKind.REMOVED_FIELD:
        field = str(detail.get("field") or detail.get("param") or "")
        if not field:
            return line
        # Remove `field=value` including optional comma
        pattern = rf",?\s*{re.escape(field)}\s*=\s*[^,)\n]+"
        updated = re.sub(pattern, "", line)
        # Clean up "(," or ",)" artifacts
        updated = re.sub(r"\(\s*,", "(", updated)
        updated = re.sub(r",\s*\)", ")", updated)
        updated = re.sub(r",\s*,", ",", updated)
        return updated

    if change.kind == ChangeKind.VALUE_DEPRECATED:
        param = str(detail.get("param") or detail.get("field") or "")
        value = detail.get("value")
        if not param or value is None:
            return line
        # Leave a clear TODO marker — auto-picking a replacement is unsafe
        marker = f"  # TODO(selfpi): deprecated value {value!r} on {param}"
        if marker.strip() in line:
            return line
        return line.rstrip("\n") + marker + ("\n" if line.endswith("\n") else "")

    if change.kind == ChangeKind.TYPE_CHANGED:
        param = str(detail.get("param") or detail.get("field") or "")
        to_type = detail.get("to_type")
        if not param:
            return line
        marker = f"  # TODO(selfpi): {param} type changed to {to_type}"
        if marker.strip() in line:
            return line
        return line.rstrip("\n") + marker + ("\n" if line.endswith("\n") else "")

    return line
