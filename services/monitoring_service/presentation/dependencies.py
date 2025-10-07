from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class Principal:
    subject: str
    scopes: set[str] = field(default_factory=set)
    roles: set[str] = field(default_factory=set)
    client_id: str | None = None


@lru_cache
def _public_key() -> str:
    path = Path(os.getenv("AUTH_PUBLIC_KEY_PATH", "/certs/auth_service.crt"))
    if not path.exists():
        raise RuntimeError(f"Public key not found at {path}")
    return path.read_text()


def _decode_token(token: str) -> Principal:
    audience = os.getenv("AUTH_JWT_AUDIENCE")
    options = {"verify_aud": bool(audience)}
    decode_kwargs = {"algorithms": ["RS256"], "options": options}
    if audience:
        decode_kwargs["audience"] = audience
    try:
        payload = jwt.decode(token, _public_key(), **decode_kwargs)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    scopes = set(filter(None, (payload.get("scope") or "").split()))
    roles = set(payload.get("roles") or [])
    return Principal(
        subject=payload.get("sub", "anonymous"),
        scopes=scopes,
        roles=roles,
        client_id=payload.get("client_id"),
    )


def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Principal:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _decode_token(credentials.credentials)


def require_scopes(*required_scopes: str) -> Callable[[Principal], Principal]:
    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not set(required_scopes).issubset(principal.scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scopes",
            )
        return principal

    return dependency


def require_roles(*required_roles: str) -> Callable[[Principal], Principal]:
    async def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if required_roles and principal.roles.isdisjoint(set(required_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return principal

    return dependency
