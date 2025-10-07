from fastapi import FastAPI

from services.common.docs import configure_openapi_security

from ..infrastructure.rate_limiting import register_rate_limiter

from .api import router
from .middleware import setup_middleware
from .metrics import setup_metrics


app = FastAPI(title="Account Service", version="0.2.0")
configure_openapi_security(
    app,
    scopes={
        "accounts:read": "Read customer and treasury account metadata",
        "accounts:write": "Create or update financial accounts",
        "transactions:read": "Link to transaction history",
    },
)
setup_middleware(app)
setup_metrics(app)
register_rate_limiter(app)
app.include_router(router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

