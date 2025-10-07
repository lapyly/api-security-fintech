from fastapi import Depends, FastAPI

from services.common.docs import configure_openapi_security

from ..infrastructure.rate_limiting import register_rate_limiter
from .api import router
from .dependencies import decode_bearer_token, get_jwt_service
from .middleware import setup_middleware
from .metrics import setup_metrics

app = FastAPI(
    title="Auth Service",
    version="0.2.0",
    description="Authentication and authorization endpoints for OAuth2 flows.",
)
configure_openapi_security(
    app,
    scopes={
        "accounts:read": "Read account resources",
        "accounts:write": "Modify account resources",
        "transactions:read": "Read transaction resources",
        "transactions:write": "Modify transaction resources",
        "audit:read": "Inspect audit events",
    },
    token_url_env="AUTH_TOKEN_URL",
    authorize_url_env="AUTH_AUTHORIZE_URL",
)

setup_middleware(app)
setup_metrics(app)
register_rate_limiter(app)
app.include_router(router)


@app.get("/health", tags=["health"], dependencies=[Depends(decode_bearer_token)])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/whoami", tags=["auth"])
async def whoami(claims: dict = Depends(decode_bearer_token)) -> dict[str, str | list[str] | None]:
    return {
        "sub": claims.get("sub"),
        "scope": claims.get("scope"),
        "roles": claims.get("roles"),
        "client_id": claims.get("client_id"),
    }


@app.get("/.well-known/jwks.json", tags=["auth"])
async def jwks(service=Depends(get_jwt_service)) -> dict:
    return service.jwks()
