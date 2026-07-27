"""Shallow-clone a GitHub repo for local scanning (prod-style connect)."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from patcher.github import GitHubAppClient

logger = logging.getLogger("selfpi.checkout")

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_MONOREPO_ROOT = _BACKEND_ROOT.parent


def _default_repo_root() -> Path:
    """Monorepo root when frontend/CLAUDE.md sit beside backend/; else backend/."""
    if (_MONOREPO_ROOT / "frontend").is_dir() or (_MONOREPO_ROOT / "CLAUDE.md").is_file():
        return _MONOREPO_ROOT
    return _BACKEND_ROOT


REPO_ROOT = _default_repo_root()


def checkout_root() -> Path:
    """Directory for GitHub clones. Override with CHECKOUT_ROOT (absolute path)."""
    override = os.environ.get("CHECKOUT_ROOT")
    if override:
        return Path(override)
    return REPO_ROOT / ".cache" / "checkouts"


# Back-compat alias for callers that import CHECKOUT_ROOT.
CHECKOUT_ROOT = checkout_root()


def checkout_path(full_name: str) -> Path:
    owner, name = full_name.split("/", 1)
    # Sanitize path segments
    owner = owner.replace("..", "").replace("/", "")
    name = name.replace("..", "").replace("/", "")
    return checkout_root() / owner / name


def ensure_github_checkout(
    full_name: str,
    *,
    installation_id: str | None = None,
    branch: str | None = None,
    token: str | None = None,
) -> Path:
    """Clone or fast-forward ``owner/name`` under ``.cache/checkouts/``.

    Uses a GitHub App installation token (same credentials as PR opening).
    """
    if "/" not in full_name:
        raise ValueError("full_name must be owner/name")

    dest = checkout_path(full_name)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if token is None:
        client = GitHubAppClient(installation_id=installation_id)
        if not client.configured:
            raise RuntimeError(
                "GitHub App not configured — cannot clone the connected repo for detection"
            )
        token = client._installation_token()

    remote = f"https://x-access-token:{token}@github.com/{full_name}.git"

    if (dest / ".git").is_dir():
        _git(["-C", str(dest), "remote", "set-url", "origin", remote])
        _git(["-C", str(dest), "fetch", "--depth", "1", "origin"], check=True)
        ref = branch or _default_branch(dest) or "HEAD"
        try:
            _git(["-C", str(dest), "checkout", "-f", f"origin/{ref}"], check=True)
        except RuntimeError:
            _git(["-C", str(dest), "checkout", "-f", "FETCH_HEAD"], check=True)
        logger.info("updated checkout %s → %s", full_name, dest)
        return dest.resolve()

    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd.extend(["--branch", branch])
    cmd.extend([remote, str(dest)])
    # Hide token in error messages
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        msg = (exc.stderr or exc.stdout or str(exc)).replace(token, "***")
        raise RuntimeError(f"git clone failed for {full_name}: {msg}") from exc
    logger.info("cloned %s → %s", full_name, dest)
    return dest.resolve()


def _default_branch(repo: Path) -> str | None:
    try:
        out = _git(["-C", str(repo), "remote", "show", "origin"], check=True)
    except RuntimeError:
        return None
    for line in out.splitlines():
        if "HEAD branch:" in line:
            return line.split(":", 1)[1].strip() or None
    return None


def _git(args: list[str], *, check: bool = False) -> str:
    # args may start with -C; prepend git
    cmd = ["git", *args] if args[0] != "git" else args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "git failed")
    return result.stdout
