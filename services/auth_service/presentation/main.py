from fastapi import Depends, FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import oauth2 as oauth2_base

from .api import router


oauth_flows = oauth2_base.OAuthFlowsModel(
    password=oauth2_base.OAuthFlowPassword(tokenUrl="/auth/token"),
    clientCredentials=oauth2_base.OAuthFlowClientCredentials(tokenUrl="/auth/token"),
)

oauth2_password_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
oauth2_client_credentials_scheme = oauth2_base.OAuth2(
    flows=oauth_flows,
    scheme_name="OAuth2PasswordAndClientCredentials",
)

app = FastAPI(
    title="Auth Service",
    version="0.1.0",
    description="Authentication and authorization endpoints for OAuth2 flows.",
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/whoami", tags=["auth"], dependencies=[Depends(oauth2_password_scheme)])
async def whoami() -> dict[str, str]:
    return {"sub": "demo-user"}


app.include_router(router)


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
            "password": {"tokenUrl": "/auth/token", "scopes": {}},
            "clientCredentials": {"tokenUrl": "/auth/token", "scopes": {}},
        },
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


default_openapi = custom_openapi
app.openapi = custom_openapi

