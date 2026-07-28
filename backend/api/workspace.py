"""Workspace scoping — which watched APIs (and their changes) are visible."""

from __future__ import annotations

from db.client import apis
from db.repos import get_connected_repo
from db.seed import DEMO_API_ID, DEMO_GITHUB_REPO
from db.settings import get_settings


def _is_harness(doc: dict) -> bool:
    """True for local Stripe demo fixtures — not a real user's watched APIs."""
    api_id = str(doc.get("_id") or "")
    if api_id == DEMO_API_ID or doc.get("mode") == "demo":
        return True
    if doc.get("source") == "seed":
        return True
    # Legacy seed docs may omit source=seed; still bound to the demo consumer.
    if doc.get("repo") == DEMO_GITHUB_REPO and doc.get("source") not in (
        "detected",
        "manual",
    ):
        return True
    return False


def visible_api_docs(*, scope: str = "workspace") -> list[dict]:
    """Filter watched APIs for the dashboard / change feed.

    scope=workspace (default) — APIs bound to the connected repo only.
    Seed harness docs and demo-mode APIs are included only when
    INCLUDE_DEMO_APIS=true.
    scope=all — every doc (debug).
    """
    docs = list(apis().find())
    if scope == "all":
        return docs

    connected = get_connected_repo()
    connected_name = (connected or {}).get("full_name")
    include_demo = bool(get_settings().include_demo_apis)

    if not connected_name:
        # Nothing connected — hide harness unless demo mode is on.
        return [d for d in docs if not _is_harness(d) or include_demo]

    out: list[dict] = []
    for doc in docs:
        if _is_harness(doc):
            if include_demo:
                out.append(doc)
            continue
        if doc.get("repo") == connected_name:
            out.append(doc)
    return out


def visible_api_ids(*, scope: str = "workspace") -> set[str]:
    return {str(d["_id"]) for d in visible_api_docs(scope=scope)}
