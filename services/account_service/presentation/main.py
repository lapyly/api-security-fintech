from fastapi import FastAPI

from ..infrastructure.rate_limiting import register_rate_limiter

from .api import router
from .middleware import setup_middleware


app = FastAPI(title="Account Service", version="0.2.0")
setup_middleware(app)
register_rate_limiter(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

