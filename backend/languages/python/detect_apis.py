"""Detect third-party APIs used by a Python repo (catalog-driven).

Deterministic, side-effect-free. Recall-first: a false positive is fine;
missing a real dependency for a catalogued vendor is not.
"""

from __future__ import annotations

import re
from pathlib import Path

from detector.catalog import ApiCatalogEntry, all_entries, get_entry

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


def _import_pattern(module: str) -> re.Pattern[str]:
    mod = re.escape(module)
    return re.compile(rf"(?m)^\s*(?:import\s+{mod}\b|from\s+{mod}(?:\.|\s))")


def _req_pattern(package: str) -> re.Pattern[str]:
    pkg = re.escape(package)
    return re.compile(rf"(?mi)^\s*{pkg}(?:\s*[\[=<~>!]| ;|$)")


def _pyproject_pattern(package: str) -> re.Pattern[str]:
    pkg = re.escape(package)
    return re.compile(
        rf"""(?mx)
        (?:^|\s|[\[,])
        ["']?{pkg}["']?
        \s*(?:=|[><=~!]|$)
        """
    )


def _pipfile_pattern(package: str) -> re.Pattern[str]:
    pkg = re.escape(package)
    return re.compile(rf"(?mi)^\s*{pkg}\s*=")


def module_in_source(source: str, module: str) -> bool:
    return bool(_import_pattern(module).search(source))


def package_in_requirements(text: str, package: str) -> bool:
    return bool(_req_pattern(package).search(text))


def package_in_pyproject(text: str, package: str) -> bool:
    return bool(_pyproject_pattern(package).search(text))


def package_in_pipfile(text: str, package: str) -> bool:
    return bool(_pipfile_pattern(package).search(text))


def package_in_dep_file(path: Path, package: str, text: str | None = None) -> bool:
    content = text if text is not None else _read_text(path)
    name = path.name.lower()
    if name == "requirements.txt" or (
        name.startswith("requirements") and name.endswith(".txt")
    ):
        return package_in_requirements(content, package)
    if name == "pyproject.toml":
        return package_in_pyproject(content, package)
    if name == "pipfile":
        return package_in_pipfile(content, package)
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
    for path in root.rglob("requirements*.txt"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.name.lower() == "requirements.txt" and path.parent == root:
            continue
        yield path


def detect_entry(repo_path: str | Path, entry: ApiCatalogEntry) -> bool:
    """True if the tree uses this catalog entry (import, dependency, or HTTP host)."""
    root = Path(repo_path)
    if not root.is_dir():
        return False

    for dep in _iter_dep_files(root):
        for package in entry.python_packages:
            if package_in_dep_file(dep, package):
                return True

    hosts = entry.http_hosts
    imports = entry.python_imports
    if not imports and not hosts:
        return False

    for py in _iter_py_files(root):
        source = _read_text(py)
        for module in imports:
            if module_in_source(source, module):
                return True
        for host in hosts:
            if host in source:
                return True

    return False


def detect_stripe(repo_path: str | Path) -> bool:
    """Back-compat helper — True if Stripe is detected."""
    entry = get_entry("stripe")
    return bool(entry and detect_entry(repo_path, entry))


def detect_apis(repo_path: str | Path) -> list[str]:
    """Return sorted list of detected catalog API ids for a Python tree."""
    found: list[str] = []
    for entry in all_entries():
        if detect_entry(repo_path, entry):
            found.append(entry.id)
    return sorted(found)
