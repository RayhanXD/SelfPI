"""Read pinned third-party package versions from a consumer checkout.

Deterministic, side-effect-free. Used to flag legacy SDK pins (e.g. openai 0.28)
that will never show up as publisher OpenAPI fingerprint diffs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
}

# requirement line: openai==0.28.1 / openai>=1.0 / openai ~= 1.2
_REQ_LINE = re.compile(
    r"""(?xi)
    ^\s*([A-Za-z0-9_.-]+)\s*
    (?:\[ [^\]]* \])?\s*
    (?:==|===|!=|<=|>=|<|>|~=)\s*
    ([^\s;#]+)
    """
)

_PYPROJECT_PIN = re.compile(
    r"""(?x)
    ["']([A-Za-z0-9_.-]+)["']\s*
    (?:==|>=|<=|~=|>|<)\s*
    ["']?([0-9][^"'\]\s,]*)
    """
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _norm_name(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def parse_version(raw: str) -> tuple[int, ...] | None:
    """Best-effort numeric version tuple from a pin like '0.28.1' or '^4.0.0'."""
    cleaned = raw.strip().lstrip("=^~>=<! ")
    cleaned = cleaned.split(",")[0].strip()
    m = re.match(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", cleaned)
    if not m:
        return None
    parts = [int(m.group(1))]
    if m.group(2) is not None:
        parts.append(int(m.group(2)))
    if m.group(3) is not None:
        parts.append(int(m.group(3)))
    return tuple(parts)


def version_less(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    """True if a < b (pad with zeros)."""
    n = max(len(a), len(b))
    aa = a + (0,) * (n - len(a))
    bb = b + (0,) * (n - len(b))
    return aa < bb


def consumer_package_versions(repo_path: str | Path) -> dict[str, str]:
    """Map normalized package name → pinned version string found in manifests."""
    root = Path(repo_path)
    if not root.is_dir():
        return {}

    found: dict[str, str] = {}

    for path in root.rglob("requirements*.txt"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        for line in _read(path).splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            m = _REQ_LINE.match(line)
            if not m:
                continue
            name, ver = _norm_name(m.group(1)), m.group(2).strip()
            found.setdefault(name, ver)

    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = _read(pyproject)
        for m in _PYPROJECT_PIN.finditer(text):
            found.setdefault(_norm_name(m.group(1)), m.group(2).strip())

    for path in root.rglob("package.json"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        try:
            data = json.loads(_read(path) or "{}")
        except json.JSONDecodeError:
            continue
        for key in ("dependencies", "devDependencies"):
            block = data.get(key) or {}
            if not isinstance(block, dict):
                continue
            for name, ver in block.items():
                if isinstance(ver, str) and ver:
                    found.setdefault(_norm_name(str(name)), ver.lstrip("^~>=<"))

    return found
