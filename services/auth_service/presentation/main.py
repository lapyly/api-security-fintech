from fastapi import Depends, FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.security import oauth2 as oauth2_base

from ..infrastructure.rate_limiting import register_rate_limiter
from .api import router
from .dependencies import decode_bearer_token, get_jwt_service
from .middleware import setup_middleware


oauth_flows = oauth2_base.OAuthFlowsModel(
    password=oauth2_base.OAuthFlowPassword(tokenUrl="/auth/token"),
    clientCredentials=oauth2_base.OAuthFlowClientCredentials(tokenUrl="/auth/token"),
)

oauth2_client_credentials_scheme = oauth2_base.OAuth2(
    flows=oauth_flows,
    scheme_name="OAuth2PasswordAndClientCredentials",
)

app = FastAPI(
    title="Auth Service",
    version="0.2.0",
    description="Authentication and authorization endpoints for OAuth2 flows.",
)

setup_middleware(app)
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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "OAuth2Password"
    ] = {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/auth/token",
                "scopes": {
                    "accounts:read": "Read account resources",
                    "accounts:write": "Modify account resources",
                    "transactions:read": "Read transaction resources",
                    "transactions:write": "Modify transaction resources",
                },
            },
            "clientCredentials": {
                "tokenUrl": "/auth/token",
                "scopes": {
                    "accounts:read": "Read account resources",
                    "accounts:write": "Modify account resources",
                    "transactions:read": "Read transaction resources",
                    "transactions:write": "Modify transaction resources",
                },
            },
        },
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


default_openapi = custom_openapi
app.openapi = custom_openapi
