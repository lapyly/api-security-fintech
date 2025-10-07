from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..application.schemas import OAuthClient
from ..application.security import JWTService, JWTSettings
from ..application.services import AuthService


bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_jwt_service() -> JWTService:
    settings = JWTSettings.from_env()
    return JWTService(settings)


def get_auth_clients() -> Iterable[OAuthClient]:
    return [
        OAuthClient(
            client_id="web-portal",
            client_name="Retail Web Portal",
            description="First-party web experience",
            scopes=["accounts:read", "transactions:read"],
            allowed_grant_types=["password", "client_credentials"],
            roles=["customer"],
        ),
        OAuthClient(
            client_id="payments-gateway",
            client_name="Payments Gateway",
            description="Handles card transactions for merchant partners",
            scopes=["transactions:write", "transactions:read"],
            allowed_grant_types=["client_credentials"],
            roles=["payments"],
        ),
        OAuthClient(
            client_id="risk-engine",
            client_name="Risk Engine",
            description="Performs fraud detection and risk scoring",
            scopes=["transactions:read", "accounts:read"],
            allowed_grant_types=["client_credentials"],
            roles=["risk"],
        ),
    ]


def get_auth_service() -> AuthService:
    return AuthService(clients=get_auth_clients(), security=get_jwt_service())


@lru_cache
def _public_key() -> str:
    public_key_path = Path(os.getenv("AUTH_PUBLIC_KEY_PATH", "/certs/auth_service.crt"))
    if not public_key_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Public key unavailable",
        )
    return public_key_path.read_text()


def decode_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    audience = os.getenv("AUTH_JWT_AUDIENCE")
    options = {"verify_aud": bool(audience)}
    decode_kwargs = {
        "algorithms": ["RS256"],
        "options": options,
    }
    if audience:
        decode_kwargs["audience"] = audience
    try:
        payload = jwt.decode(
            token,
            _public_key(),
            **decode_kwargs,
        )
    except jwt.PyJWTError as exc:  # pragma: no cover - runtime protection
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return payload
