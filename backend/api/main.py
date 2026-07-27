"""FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import (
    apis_router,
    auth_router,
    changes_router,
    repos_router,
    settings_router,
    specs_router,
)
from db.client import get_client
from db.schemas import ensure_indexes
from db.settings import get_settings
from watcher.scheduler import watch_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("selfpi.api")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    client = get_client()
    ensure_indexes(client[settings.mongodb_db])

    stop = asyncio.Event()
    watch_task: asyncio.Task | None = None
    if settings.watch_enabled and int(settings.watch_interval_seconds or 0) > 0:
        watch_task = asyncio.create_task(watch_loop(stop), name="selfpi-watch-loop")
        logger.info(
            "scheduled watcher enabled (interval=%ss)",
            settings.watch_interval_seconds,
        )
    else:
        logger.info("scheduled watcher disabled")

    try:
        yield
    finally:
        stop.set()
        if watch_task is not None:
            watch_task.cancel()
            try:
                await watch_task
            except asyncio.CancelledError:
                pass
        client.close()


app = FastAPI(
    title="SelfPI",
    description="Self-Maintaining APIs — REST layer (docs/API_CONTRACT.md)",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(apis_router)
app.include_router(changes_router)
app.include_router(specs_router)
app.include_router(settings_router)
app.include_router(repos_router)
app.include_router(auth_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": str(exc)}},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    s = get_settings()
    uvicorn.run("api.main:app", host=s.api_host, port=s.api_port, reload=True)


if __name__ == "__main__":
    run()
