"""Background poller for live watched APIs.

Runs inside the FastAPI lifespan as a single asyncio task. Polls only live
(non-demo) APIs that have a `spec_url`. Reuses `poll_api` + `pr_pipeline_flags`
so PRs open only when GitHub is configured and call sites exist.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from db.client import apis
from db.settings import get_settings, pr_pipeline_flags

logger = logging.getLogger("selfpi.watcher")


def live_api_ids() -> list[str]:
    """IDs of watched APIs that should be polled on a schedule.

    Live mode with a spec_url. Demo APIs (Bump only) are never auto-polled.
    """
    ids: list[str] = []
    for doc in apis().find():
        mode = (doc.get("mode") or "").strip().lower()
        if mode == "demo":
            continue
        if not doc.get("spec_url"):
            continue
        if mode and mode != "live":
            continue
        ids.append(str(doc["_id"]))
    return ids


def poll_live_apis(*, open_pr: bool | None = None, dry_run_pr: bool | None = None) -> dict[str, Any]:
    """Poll every live watched API once. Returns a summary for logging/tests."""
    # Local import avoids circular import with watcher.__init__
    from watcher import poll_api

    if open_pr is None or dry_run_pr is None:
        flags = pr_pipeline_flags()
        open_pr = flags[0] if open_pr is None else open_pr
        dry_run_pr = flags[1] if dry_run_pr is None else dry_run_pr

    results: list[dict[str, Any]] = []
    ids = live_api_ids()
    logger.info(
        "watch poll starting: %d live api(s), open_pr=%s",
        len(ids),
        open_pr,
    )
    for api_id in ids:
        try:
            outcome = poll_api(api_id, open_pr=open_pr, dry_run_pr=dry_run_pr)
            entry = {
                "api_id": api_id,
                "ok": True,
                "new_version": outcome.get("new_version"),
                "changes_detected": int(outcome.get("changes_detected") or 0),
            }
            if entry["new_version"]:
                logger.info(
                    "watch poll %s: new version %s (%d change(s))",
                    api_id,
                    entry["new_version"],
                    entry["changes_detected"],
                )
            else:
                logger.info("watch poll %s: no change", api_id)
        except Exception as exc:  # noqa: BLE001 — keep loop alive
            logger.exception("watch poll %s failed: %s", api_id, exc)
            entry = {"api_id": api_id, "ok": False, "error": str(exc)}
        results.append(entry)

    changed = sum(1 for r in results if r.get("ok") and r.get("new_version"))
    failed = sum(1 for r in results if not r.get("ok"))
    logger.info(
        "watch poll finished: checked=%d changed=%d failed=%d",
        len(results),
        changed,
        failed,
    )
    return {
        "checked": len(results),
        "changed": changed,
        "failed": failed,
        "results": results,
    }


async def watch_loop(stop: asyncio.Event) -> None:
    """Periodically poll live APIs until `stop` is set."""
    settings = get_settings()
    interval = max(5, int(settings.watch_interval_seconds or 300))
    logger.info("watch loop started (interval=%ss)", interval)
    # First tick after a short delay so startup / seed can finish.
    try:
        await asyncio.wait_for(stop.wait(), timeout=min(5, interval))
        return
    except asyncio.TimeoutError:
        pass

    while not stop.is_set():
        try:
            await asyncio.to_thread(poll_live_apis)
        except Exception:  # noqa: BLE001
            logger.exception("watch loop iteration crashed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            continue
    logger.info("watch loop stopped")
