from __future__ import annotations

import os
from typing import Mapping

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def configure_openapi_security(
    app: FastAPI,
    *,
    scopes: Mapping[str, str],
    token_url_env: str = "AUTH_TOKEN_URL",
    authorize_url_env: str = "AUTH_AUTHORIZE_URL",
    client_id_env: str = "DOCS_OAUTH_CLIENT_ID",
) -> None:
    """Augment a FastAPI app with OAuth2 documentation helpers."""

    token_url = os.getenv(token_url_env, "https://auth.local/auth/token")
    authorize_url = os.getenv(authorize_url_env, "https://auth.local/oauth/authorize")
    client_id = os.getenv(client_id_env, "web-portal")

    oauth2_scheme = {
        "type": "oauth2",
        "flows": {
            "authorizationCode": {
                "authorizationUrl": authorize_url,
                "tokenUrl": token_url,
                "scopes": scopes,
            },
            "clientCredentials": {
                "tokenUrl": token_url,
                "scopes": scopes,
            },
        },
    }

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        components = openapi_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["OAuth2"] = oauth2_scheme
        openapi_schema.setdefault("security", []).append({"OAuth2": []})
        app.openapi_schema = openapi_schema
        return openapi_schema

    app.openapi = custom_openapi  # type: ignore[assignment]
    app.swagger_ui_init_oauth = {  # type: ignore[attr-defined]
        "clientId": client_id,
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": scopes,
    }
