"""Detect third-party APIs used by a Python repo (v1: Stripe only).

Deterministic, side-effect-free. Recall-first: a false positive is fine;
missing a real Stripe dependency is not.
"""

from __future__ import annotations

import re
from pathlib import Path

# import stripe / import stripe as X / import stripe, other
# from stripe import … / from stripe.xxx import …
_IMPORT_STRIPE = re.compile(
    r"(?m)^\s*(?:import\s+stripe\b|from\s+stripe(?:\.|\s))",
)

# requirements.txt / constraints style: stripe, stripe==x, stripe[extra]>=…
_REQ_STRIPE = re.compile(
    r"(?mi)^\s*stripe(?:\s*[\[=<~>!]| ;|$)",
)

# pyproject.toml: "stripe", 'stripe', stripe = "…"
_PYPROJECT_STRIPE = re.compile(
    r"""(?mx)
    (?:^|\s|[\[,])
    ["']?stripe["']?
    \s*(?:=|[><=~!]|$)
    """,
)

# Pipfile: stripe = "*"
_PIPFILE_STRIPE = re.compile(
    r'(?m)^\s*stripe\s*=',
)

_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    ".eggs",
}

_DEP_FILES = ("requirements.txt", "pyproject.toml", "Pipfile")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def stripe_in_source(source: str) -> bool:
    """True if source has an import/from stripe statement."""
    return bool(_IMPORT_STRIPE.search(source))


def stripe_in_requirements(text: str) -> bool:
    return bool(_REQ_STRIPE.search(text))


def stripe_in_pyproject(text: str) -> bool:
    return bool(_PYPROJECT_STRIPE.search(text))


def stripe_in_pipfile(text: str) -> bool:
    return bool(_PIPFILE_STRIPE.search(text))


def stripe_in_dep_file(path: Path, text: str | None = None) -> bool:
    """Detect stripe in a known dependency manifest by filename."""
    content = text if text is not None else _read_text(path)
    name = path.name.lower()
    if name == "requirements.txt" or name.startswith("requirements") and name.endswith(".txt"):
        return stripe_in_requirements(content)
    if name == "pyproject.toml":
        return stripe_in_pyproject(content)
    if name == "pipfile":
        return stripe_in_pipfile(content)
    return False


def _iter_py_files(root: Path):
    for path in root.rglob("*.py"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def _iter_dep_files(root: Path):
    for name in _DEP_FILES:
        candidate = root / name
        if candidate.is_file():
            yield candidate
    # nested requirements*.txt one level deep is uncommon; still scan tree lightly
    for path in root.rglob("requirements*.txt"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.name.lower() == "requirements.txt" and path.parent == root:
            continue  # already yielded
        yield path


def detect_stripe(repo_path: str | Path) -> bool:
    """Return True if the tree under repo_path uses Stripe (import and/or dep)."""
    root = Path(repo_path)
    if not root.is_dir():
        return False

    for dep in _iter_dep_files(root):
        if stripe_in_dep_file(dep):
            return True

    for py in _iter_py_files(root):
        if stripe_in_source(_read_text(py)):
            return True

    return False


def detect_apis(repo_path: str | Path) -> list[str]:
    """Return sorted list of detected API ids for a Python tree (v1: stripe)."""
    found: list[str] = []
    if detect_stripe(repo_path):
        found.append("stripe")
    return found
