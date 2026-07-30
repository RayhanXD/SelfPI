"""TypeScript / JavaScript language module — detection fingerprints.

Call-site scanning for TS is not in v1; this module exists so the detector
can discover npm / fetch-based API usage (CLAUDE.md: extend by module).
"""

from __future__ import annotations

from languages.typescript.detect_apis import detect_apis

LANGUAGE = "typescript"
name = "typescript"

__all__ = ["LANGUAGE", "name", "detect_apis"]
