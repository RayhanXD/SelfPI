"""LLM client — Anthropic Messages API. Isolated from deterministic core."""

from __future__ import annotations

import json
import re
from typing import Any, Protocol

import httpx

from db.settings import get_settings


class LlmClient(Protocol):
    def complete_json(self, *, system: str, user: str) -> dict[str, Any]: ...


class AnthropicClient:
    """Thin Anthropic Messages wrapper. Returns parsed JSON object from the model."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        base_url: str = "https://api.anthropic.com",
    ):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self.base_url = base_url.rstrip("/")

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(f"{self.base_url}/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        return _extract_json(text)


class HeuristicClient:
    """Offline stand-in used when no API key is configured (tests / local)."""

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        # Adjudicator shape
        if "confirm or reject" in system.lower() or "adjudic" in system.lower():
            try:
                payload = json.loads(user)
            except json.JSONDecodeError:
                return {"decisions": []}
            decisions = []
            for c in payload.get("candidates", []):
                reject = bool(c.get("in_comment") or c.get("in_string"))
                decisions.append(
                    {
                        "id": c.get("id"),
                        "decision": "reject" if reject else "confirm",
                        "reason": "comment/string" if reject else "heuristic_confirm",
                    }
                )
            return {"decisions": decisions}

        # Patcher explanation shape
        return {
            "title": "fix: update call sites for API breaking change",
            "body": "Automated patch from SelfPI.\n\n" + user[:500],
            "edits": [],
        }


def get_llm_client() -> LlmClient:
    settings = get_settings()
    if settings.anthropic_api_key:
        return AnthropicClient()
    return HeuristicClient()


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return json.loads(fence.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"Model response was not JSON: {text[:200]!r}")
