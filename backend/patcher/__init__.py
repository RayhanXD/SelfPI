"""Patcher — generate fixes for confirmed call sites and open a GitHub PR.

Mechanical edits are deterministic (renamed_param / removed_field / …).
LLM supplies PR title/body when configured; otherwise a template is used.
GitHub App opens the PR when credentials are present.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from diff.types import BreakingChange
from llm.client import LlmClient, get_llm_client
from patcher.github import GitHubAppClient
from patcher.patches import FileEdit, apply_edits, build_edits
from scanner.ir.types import CallSite

_PR_SYSTEM = """You write GitHub pull request copy for SelfPI.
Given a breaking change and the files edited, return JSON only:
{"title":"...","body":"markdown explanation of what changed and why"}
Do not invent extra file edits.
"""


def generate_patches(
    repo_path: str | Path,
    call_sites: list[CallSite],
    change: BreakingChange,
) -> list[FileEdit]:
    """Build mechanical file edits (does not write to disk)."""
    return build_edits(repo_path, call_sites, change)


def apply_patches_locally(
    repo_path: str | Path,
    call_sites: list[CallSite],
    change: BreakingChange,
) -> list[str]:
    """Apply mechanical patches to a local checkout. Returns edited relative paths."""
    edits = build_edits(repo_path, call_sites, change)
    return apply_edits(repo_path, edits)


def generate_and_open_pr(
    call_sites: list[CallSite],
    change: BreakingChange,
    *,
    repo: str,
    repo_path: str | Path,
    base_branch: str | None = None,
    dry_run: bool = False,
    llm: LlmClient | None = None,
    github: GitHubAppClient | None = None,
) -> dict[str, Any]:
    """Generate a fix for confirmed call sites and open a PR (or dry-run locally).

    Returns PR metadata matching the API contract `pr` embed shape, plus
    `edited_files` and `dry_run`.
    """
    from db.settings import get_settings

    edits = build_edits(repo_path, call_sites, change)
    title, body = _pr_copy(call_sites, change, edits, llm=llm)
    commit_message = title
    # Optional override only — GitHubAppClient resolves repo default_branch when None.
    settings = get_settings()
    preferred_base = base_branch if base_branch is not None else (
        settings.github_default_base_branch.strip() or None
        if settings.github_default_base_branch
        else None
    )

    if dry_run or not edits:
        if dry_run and edits:
            apply_edits(repo_path, edits)
        return {
            "number": 0,
            "url": None,
            "state": "open",
            "tests_passing": None,
            "opened_at": _now(),
            "dry_run": True,
            "edited_files": [e.path for e in edits],
            "title": title,
            "body": body,
        }

    client = github or GitHubAppClient()
    if not client.configured:
        # Local fallback when App isn't configured
        apply_edits(repo_path, edits)
        return {
            "number": 0,
            "url": None,
            "state": "open",
            "tests_passing": None,
            "opened_at": _now(),
            "dry_run": True,
            "edited_files": [e.path for e in edits],
            "title": title,
            "body": body,
            "note": "GitHub App not configured; applied locally as dry-run",
        }

    head = f"selfpi/{change.operation_id}-{change.kind.value}".replace("_", "-")[:60]
    files = {e.path: e.new_content for e in edits}
    pr = client.create_pull_request(
        repo=repo,
        base_branch=preferred_base,
        head_branch=head,
        title=title,
        body=body,
        files=files,
        commit_message=commit_message,
    )
    pr.update(
        {
            "dry_run": False,
            "edited_files": list(files),
            "title": title,
            "body": body,
        }
    )
    return pr


def _pr_copy(
    call_sites: list[CallSite],
    change: BreakingChange,
    edits: list[FileEdit],
    *,
    llm: LlmClient | None,
) -> tuple[str, str]:
    default_title = f"fix: {change.kind.value} on {change.operation_id}"
    default_body = _template_body(call_sites, change, edits)

    client = llm or get_llm_client()
    # HeuristicClient always returns something; Anthropic only when keyed.
    try:
        result = client.complete_json(
            system=_PR_SYSTEM,
            user=json.dumps(
                {
                    "change": change.model_dump(mode="json"),
                    "call_sites": [
                        {"file": s.file, "line": s.span.start_line, "snippet": s.snippet}
                        for s in call_sites
                    ],
                    "edited_files": [e.path for e in edits],
                },
                indent=2,
            ),
        )
        title = str(result.get("title") or default_title)
        body = str(result.get("body") or default_body)
        return title, body
    except Exception:
        return default_title, default_body


def _template_body(
    call_sites: list[CallSite], change: BreakingChange, edits: list[FileEdit]
) -> str:
    lines = [
        "## Summary",
        f"SelfPI detected a `{change.kind.value}` on `{change.operation_id}`.",
        "",
        f"Detail: `{json.dumps(change.detail)}`",
        "",
        f"## Call sites ({len(call_sites)})",
    ]
    for s in call_sites:
        lines.append(f"- `{s.file}:{s.span.start_line}` — `{s.snippet}`")
    lines.extend(["", "## Files edited", ""])
    for e in edits:
        lines.append(f"- `{e.path}`")
    lines.extend(
        [
            "",
            "## Test plan",
            "- [ ] Repo tests pass on this branch",
            "- [ ] Call sites no longer use the breaking surface",
        ]
    )
    return "\n".join(lines)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
