"""Adjudicator — bounded LLM review of gray-zone CallSite records.

Only confirms/rejects candidates the deterministic layers already produced.
Never scans the repo on its own.
"""

from __future__ import annotations

import json
from typing import Any

from llm.client import LlmClient, get_llm_client
from scanner.ir.enums import SourceLayer
from scanner.ir.types import CallSite

# FRONTEND_GUIDELINES confidence scale: >= 0.85 high (auto-include)
AUTO_INCLUDE_THRESHOLD = 0.85

_SYSTEM = """You are the SelfPI adjudicator.
You receive CallSite IR records already found by a deterministic scanner.
Confirm or reject each candidate. Never invent new call sites or scan a repo.
Respond with JSON only:
{"decisions":[{"id":"...","decision":"confirm"|"reject","reason":"..."}]}
"""


def adjudicate(
    candidates: list[CallSite],
    *,
    change_context: dict | None = None,
    llm: LlmClient | None = None,
    auto_threshold: float = AUTO_INCLUDE_THRESHOLD,
) -> list[CallSite]:
    """Confirm or reject gray-zone records. Returns confirmed CallSites only.

    High-confidence sites (>= auto_threshold) are auto-included.
    Gray-zone sites are sent to the LLM (or heuristic client).
    """
    if not candidates:
        return []

    auto: list[CallSite] = []
    gray: list[CallSite] = []
    for site in candidates:
        conf = site.confidence if site.confidence is not None else 0.0
        if conf >= auto_threshold and not site.in_comment:
            auto.append(site)
        else:
            gray.append(site)

    if not gray:
        return auto

    client = llm or get_llm_client()
    payload = {
        "change": change_context or {},
        "candidates": [_site_payload(s) for s in gray],
    }
    result = client.complete_json(
        system=_SYSTEM,
        user=json.dumps(payload, indent=2),
    )
    decisions = {
        d.get("id"): d
        for d in (result.get("decisions") or [])
        if isinstance(d, dict) and d.get("id")
    }

    confirmed = list(auto)
    for site in gray:
        decision = decisions.get(site.id or "")
        if decision is None:
            # Fail closed on missing decision only for very low confidence;
            # otherwise keep (recall-first among already-surfaced candidates).
            if (site.confidence or 0) >= 0.5 and not site.in_comment:
                confirmed.append(
                    site.model_copy(
                        update={"source_layer": SourceLayer.AGENT, "confidence": site.confidence}
                    )
                )
            continue
        if str(decision.get("decision", "")).lower() == "confirm":
            confirmed.append(
                site.model_copy(
                    update={
                        "source_layer": SourceLayer.AGENT,
                        "confidence": max(site.confidence or 0.0, 0.7),
                    }
                )
            )
    return confirmed


def _site_payload(site: CallSite) -> dict[str, Any]:
    return {
        "id": site.id,
        "file": site.file,
        "span": site.span.model_dump(),
        "receiver": site.receiver,
        "path": site.path,
        "operation_id": site.operation_id,
        "args": [a.model_dump(mode="json") for a in site.args],
        "snippet": site.snippet,
        "in_comment": site.in_comment,
        "in_string": site.in_string,
        "confidence": site.confidence,
        "source_layer": site.source_layer.value if site.source_layer else None,
    }
