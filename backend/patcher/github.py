"""GitHub App client — installation tokens, branch, commit, open PR."""

from __future__ import annotations

import time
from typing import Any

import httpx

from db.settings import get_settings

try:
    import jwt
except ImportError:  # pragma: no cover
    jwt = None  # type: ignore


class GitHubAppClient:
    """Minimal GitHub App API for opening fix PRs."""

    def __init__(
        self,
        *,
        app_id: str | None = None,
        private_key: str | None = None,
        installation_id: str | None = None,
        api_url: str = "https://api.github.com",
    ):
        settings = get_settings()
        self.app_id = app_id if app_id is not None else settings.github_app_id
        self.private_key = (
            private_key if private_key is not None else settings.github_app_private_key
        )
        self.installation_id = (
            installation_id
            if installation_id is not None
            else settings.github_app_installation_id
        )
        self.api_url = api_url.rstrip("/")
        self._token: str | None = None
        self._token_expires_at = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.app_id and self.private_key and self.installation_id)

    def create_pull_request(
        self,
        *,
        repo: str,
        head_branch: str,
        title: str,
        body: str,
        files: dict[str, str],
        commit_message: str,
        base_branch: str | None = None,
    ) -> dict[str, Any]:
        """Create branch from base, commit file contents, open PR.

        `files` maps path → full new file content.
        `repo` is `owner/name`.
        `base_branch` is optional — when omitted (or missing on the remote),
        uses the repository's GitHub `default_branch` (main/master/whatever).
        """
        if not self.configured:
            raise RuntimeError(
                "GitHub App not configured "
                "(GITHUB_APP_ID / GITHUB_APP_PRIVATE_KEY / GITHUB_APP_INSTALLATION_ID)"
            )

        owner, name = repo.split("/", 1)
        token = self._installation_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        with httpx.Client(timeout=60.0, headers=headers) as client:
            base_branch = self._resolve_base_branch(client, owner, name, base_branch)
            base_ref = client.get(f"{self.api_url}/repos/{owner}/{name}/git/ref/heads/{base_branch}")
            base_ref.raise_for_status()
            base_sha = base_ref.json()["object"]["sha"]

            base_commit = client.get(
                f"{self.api_url}/repos/{owner}/{name}/git/commits/{base_sha}"
            )
            base_commit.raise_for_status()
            base_tree = base_commit.json()["tree"]["sha"]

            tree_items = []
            for path, content in files.items():
                blob = client.post(
                    f"{self.api_url}/repos/{owner}/{name}/git/blobs",
                    json={"content": content, "encoding": "utf-8"},
                )
                blob.raise_for_status()
                tree_items.append(
                    {
                        "path": path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob.json()["sha"],
                    }
                )

            tree = client.post(
                f"{self.api_url}/repos/{owner}/{name}/git/trees",
                json={"base_tree": base_tree, "tree": tree_items},
            )
            tree.raise_for_status()
            tree_sha = tree.json()["sha"]

            commit = client.post(
                f"{self.api_url}/repos/{owner}/{name}/git/commits",
                json={
                    "message": commit_message,
                    "tree": tree_sha,
                    "parents": [base_sha],
                },
            )
            commit.raise_for_status()
            commit_sha = commit.json()["sha"]

            ref = client.post(
                f"{self.api_url}/repos/{owner}/{name}/git/refs",
                json={"ref": f"refs/heads/{head_branch}", "sha": commit_sha},
            )
            if ref.status_code == 422:
                # Branch exists — update it
                ref = client.patch(
                    f"{self.api_url}/repos/{owner}/{name}/git/refs/heads/{head_branch}",
                    json={"sha": commit_sha, "force": True},
                )
            ref.raise_for_status()

            pr = client.post(
                f"{self.api_url}/repos/{owner}/{name}/pulls",
                json={
                    "title": title,
                    "head": head_branch,
                    "base": base_branch,
                    "body": body,
                },
            )
            pr.raise_for_status()
            data = pr.json()
            return {
                "number": data["number"],
                "url": data.get("html_url"),
                "state": data.get("state", "open"),
                "tests_passing": None,
                "opened_at": data.get("created_at"),
                "base_branch": base_branch,
            }

    def _resolve_base_branch(
        self,
        client: httpx.Client,
        owner: str,
        name: str,
        preferred: str | None,
    ) -> str:
        """Use preferred branch if it exists; otherwise the repo default_branch."""
        repo_info = client.get(f"{self.api_url}/repos/{owner}/{name}")
        repo_info.raise_for_status()
        default = (repo_info.json().get("default_branch") or "").strip()
        if not default:
            raise RuntimeError(f"Repository {owner}/{name} has no default_branch")

        candidates: list[str] = []
        if preferred and preferred.strip():
            candidates.append(preferred.strip())
        if default not in candidates:
            candidates.append(default)

        last_error: Exception | None = None
        for branch in candidates:
            ref = client.get(f"{self.api_url}/repos/{owner}/{name}/git/ref/heads/{branch}")
            if ref.status_code == 200:
                return branch
            last_error = httpx.HTTPStatusError(
                f"Branch '{branch}' not found on {owner}/{name}",
                request=ref.request,
                response=ref,
            )
        assert last_error is not None
        raise last_error

    def _installation_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        if jwt is None:
            raise RuntimeError(
                "PyJWT is required for GitHub App auth — pip install PyJWT cryptography"
            )

        app_jwt = jwt.encode(
            {
                "iat": int(now) - 60,
                "exp": int(now) + 9 * 60,
                "iss": self.app_id,
            },
            self.private_key.replace("\\n", "\n"),
            algorithm="RS256",
        )
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
        }
        with httpx.Client(timeout=30.0, headers=headers) as client:
            resp = client.post(
                f"{self.api_url}/app/installations/{self.installation_id}/access_tokens"
            )
            resp.raise_for_status()
            data = resp.json()
        self._token = data["token"]
        # tokens last ~1h
        self._token_expires_at = now + 3600
        return self._token
