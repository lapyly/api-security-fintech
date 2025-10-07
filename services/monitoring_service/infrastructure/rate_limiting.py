from __future__ import annotations

import os
from typing import Optional

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter


async def init_rate_limiter(redis_url: Optional[str] = None) -> None:
    if FastAPILimiter.redis:  # type: ignore[attr-defined]
        return
    url = redis_url or os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = redis.from_url(url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)


def register_rate_limiter(app: FastAPI) -> None:
    @app.on_event("startup")
    async def _startup() -> None:
        await init_rate_limiter()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        if FastAPILimiter.redis:  # type: ignore[attr-defined]
            await FastAPILimiter.close()
