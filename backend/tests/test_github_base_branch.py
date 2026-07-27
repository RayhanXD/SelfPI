"""GitHub App client — resolve base branch from repo default."""

from __future__ import annotations

import httpx

from patcher.github import GitHubAppClient


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, url: str = "https://api.github.com/fake"):
        self.status_code = status_code
        self._payload = payload or {}
        self.request = httpx.Request("GET", url)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=self.request,
                response=httpx.Response(self.status_code, request=self.request),
            )


class _FakeClient:
    def __init__(self, routes: dict[str, _FakeResponse]):
        self.routes = routes

    def get(self, url: str):
        # Longest-key match so .../git/ref/heads/X wins over .../repos/owner/name
        matches = [(k, r) for k, r in self.routes.items() if k in url]
        if not matches:
            return _FakeResponse(404, url=url)
        matches.sort(key=lambda item: len(item[0]), reverse=True)
        return matches[0][1]


def test_resolve_base_uses_repo_default_when_preferred_missing():
    client = GitHubAppClient(app_id="1", private_key="k", installation_id="2")
    fake = _FakeClient(
        {
            "/repos/acme/app": _FakeResponse(200, {"default_branch": "trunk"}),
            "/git/ref/heads/trunk": _FakeResponse(200, {"object": {"sha": "abc"}}),
        }
    )
    assert client._resolve_base_branch(fake, "acme", "app", None) == "trunk"  # type: ignore[arg-type]


def test_resolve_base_falls_back_when_preferred_404():
    client = GitHubAppClient(app_id="1", private_key="k", installation_id="2")
    fake = _FakeClient(
        {
            "/repos/acme/app": _FakeResponse(200, {"default_branch": "master"}),
            "/git/ref/heads/main": _FakeResponse(404),
            "/git/ref/heads/master": _FakeResponse(200, {"object": {"sha": "abc"}}),
        }
    )
    assert client._resolve_base_branch(fake, "acme", "app", "main") == "master"  # type: ignore[arg-type]


def test_resolve_base_keeps_preferred_when_it_exists():
    client = GitHubAppClient(app_id="1", private_key="k", installation_id="2")
    fake = _FakeClient(
        {
            "/repos/acme/app": _FakeResponse(200, {"default_branch": "master"}),
            "/git/ref/heads/develop": _FakeResponse(200, {"object": {"sha": "abc"}}),
            "/git/ref/heads/master": _FakeResponse(200, {"object": {"sha": "def"}}),
        }
    )
    assert client._resolve_base_branch(fake, "acme", "app", "develop") == "develop"  # type: ignore[arg-type]
