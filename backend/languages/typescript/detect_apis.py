"""Detect third-party APIs used by a JS/TS repo (catalog-driven).

Deterministic, side-effect-free. Recall-first: a false positive is fine;
missing a real npm dependency or raw HTTP host for a catalogued vendor is not.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from detector.catalog import ApiCatalogEntry, all_entries

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
    ".next",
    ".nuxt",
    "coverage",
    ".turbo",
}

_SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _iter_source_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _SOURCE_SUFFIXES:
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        yield path


def _package_json_paths(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("package.json"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        found.append(path)
    return found


def _deps_from_package_json(path: Path) -> set[str]:
    raw = _read_text(path)
    if not raw:
        return set()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return set()
    names: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        block = data.get(key) or {}
        if isinstance(block, dict):
            names.update(str(k) for k in block)
    return names


def _npm_import_pattern(package: str) -> re.Pattern[str]:
    """Match ESM/CJS imports of an npm package or a subpath of it."""
    pkg = re.escape(package)
    # from "pkg" | from 'pkg/foo' | require("pkg") | import("pkg")
    return re.compile(
        rf"""(?x)
        (?:
            \bfrom\s+["']{pkg}(?:/[^"']*)?["']
          | \brequire\s*\(\s*["']{pkg}(?:/[^"']*)?["']
          | \bimport\s*\(\s*["']{pkg}(?:/[^"']*)?["']
        )
        """
    )


def npm_in_deps(deps: set[str], package: str) -> bool:
    return package in deps


def module_in_js_source(source: str, module: str) -> bool:
    return bool(_npm_import_pattern(module).search(source))


def host_in_source(source: str, host: str) -> bool:
    return host in source


def detect_entry(repo_path: str | Path, entry: ApiCatalogEntry) -> bool:
    """True if the tree uses this catalog entry via npm, JS import, or HTTP host."""
    root = Path(repo_path)
    if not root.is_dir():
        return False

    has_npm = bool(entry.npm_packages)
    has_js = bool(entry.js_imports)
    has_hosts = bool(entry.http_hosts)
    if not (has_npm or has_js or has_hosts):
        return False

    deps: set[str] = set()
    for pkg_json in _package_json_paths(root):
        deps |= _deps_from_package_json(pkg_json)

    if has_npm:
        for package in entry.npm_packages:
            if npm_in_deps(deps, package):
                return True

    if not (has_js or has_hosts):
        return False

    for path in _iter_source_files(root):
        source = _read_text(path)
        if not source:
            continue
        if has_js:
            for module in entry.js_imports:
                if module_in_js_source(source, module):
                    return True
        if has_hosts:
            for host in entry.http_hosts:
                if host_in_source(source, host):
                    return True

    return False


def detect_apis(repo_path: str | Path) -> list[str]:
    """Return sorted list of detected catalog API ids for a JS/TS tree."""
    found: list[str] = []
    for entry in all_entries():
        if detect_entry(repo_path, entry):
            found.append(entry.id)
    return sorted(found)
