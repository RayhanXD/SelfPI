"""Known third-party APIs — detection fingerprints + OpenAPI URLs.

Extend by appending an ApiCatalogEntry. Do not scatter vendor-specific
import/package strings through the pipeline (CLAUDE.md: extend by module).

Call-site surface maps live under languages/python/surfaces.py and are optional:
an API can be detected and watched before its SDK→operation_id map exists.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiCatalogEntry:
    id: str
    name: str
    spec_url: str
    # Pip / dependency names (matched case-insensitively in manifests).
    python_packages: tuple[str, ...]
    # Top-level import modules (`import X`, `from X import …`).
    python_imports: tuple[str, ...]

    @property
    def watchable(self) -> bool:
        """True when we have a fetchable OpenAPI URL."""
        return bool(self.spec_url.strip())


STRIPE_SPEC_URL = (
    "https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json"
)

_CATALOG: tuple[ApiCatalogEntry, ...] = (
    ApiCatalogEntry(
        id="stripe",
        name="Stripe",
        spec_url=STRIPE_SPEC_URL,
        python_packages=("stripe",),
        python_imports=("stripe",),
    ),
    ApiCatalogEntry(
        id="openai",
        name="OpenAI",
        spec_url=(
            "https://raw.githubusercontent.com/openai/openai-openapi/master/openapi.yaml"
        ),
        python_packages=("openai",),
        python_imports=("openai",),
    ),
    ApiCatalogEntry(
        id="twilio",
        name="Twilio",
        spec_url=(
            "https://raw.githubusercontent.com/twilio/twilio-oai/main/spec/json/"
            "twilio_api_v2010.json"
        ),
        python_packages=("twilio",),
        python_imports=("twilio",),
    ),
    ApiCatalogEntry(
        id="github",
        name="GitHub",
        spec_url=(
            "https://raw.githubusercontent.com/github/rest-api-description/main/"
            "descriptions/api.github.com/api.github.com.json"
        ),
        python_packages=("PyGithub", "pygithub"),
        python_imports=("github",),
    ),
    ApiCatalogEntry(
        id="slack",
        name="Slack",
        spec_url=(
            "https://raw.githubusercontent.com/slackapi/slack-api-specs/master/"
            "web-api/slack_web_openapi_v2.json"
        ),
        python_packages=("slack_sdk", "slack-sdk", "slackclient"),
        python_imports=("slack_sdk", "slack"),
    ),
    ApiCatalogEntry(
        id="discord",
        name="Discord",
        spec_url=(
            "https://raw.githubusercontent.com/discord/discord-api-spec/main/"
            "specs/openapi.json"
        ),
        python_packages=("discord.py", "discord-py"),
        python_imports=("discord",),
    ),
    ApiCatalogEntry(
        id="plaid",
        name="Plaid",
        spec_url=(
            "https://raw.githubusercontent.com/plaid/plaid-openapi/master/2020-09-14.yml"
        ),
        python_packages=("plaid-python", "plaid"),
        python_imports=("plaid",),
    ),
    ApiCatalogEntry(
        id="square",
        name="Square",
        spec_url=(
            "https://raw.githubusercontent.com/square/connect-api-specification/"
            "master/api.json"
        ),
        python_packages=("squareup", "square"),
        python_imports=("square",),
    ),
    # Detectable today; no stable public OpenAPI URL yet — watchable=False.
    # Appears in detected_apis so the UI can prompt to add a spec_url manually.
    ApiCatalogEntry(
        id="anthropic",
        name="Anthropic",
        spec_url="",
        python_packages=("anthropic",),
        python_imports=("anthropic",),
    ),
)


def all_entries() -> tuple[ApiCatalogEntry, ...]:
    return _CATALOG


def get_entry(api_id: str) -> ApiCatalogEntry | None:
    for entry in _CATALOG:
        if entry.id == api_id:
            return entry
    return None


def catalog_ids() -> frozenset[str]:
    return frozenset(e.id for e in _CATALOG)


def python_sdk_roots() -> tuple[str, ...]:
    """All import roots — used by the Python scanner prefilter."""
    roots: list[str] = []
    seen: set[str] = set()
    for entry in _CATALOG:
        for mod in entry.python_imports:
            if mod not in seen:
                seen.add(mod)
                roots.append(mod)
    return tuple(roots)
