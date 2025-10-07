from fastapi import FastAPI

from services.common.docs import configure_openapi_security

from ..infrastructure.rate_limiting import register_rate_limiter

from .api import router
from .middleware import setup_middleware
from .metrics import setup_metrics


app = FastAPI(title="Transaction Service", version="0.2.0")
configure_openapi_security(
    app,
    scopes={
        "transactions:read": "Read transaction records",
        "transactions:write": "Create or update transactions",
        "accounts:read": "Read account metadata for transaction context",
    },
)
setup_middleware(app)
setup_metrics(app)
register_rate_limiter(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

