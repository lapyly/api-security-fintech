from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    issued_at: datetime


class ClientRegistration(BaseModel):
    client_id: str
    client_name: str
    scopes: list[str]
    created_at: datetime


class TokenRevocationRequest(BaseModel):
    token: str
    token_type_hint: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    scope: Optional[str] = None
    expires_in: Optional[int] = None


class TokenRequestMeta(BaseModel):
    client_id: Optional[str] = None
    grant_type: str
    requested_scope: Optional[str] = None
    audience: Optional[str] = None


class OAuthClient(BaseModel):
    client_id: str
    client_name: str
    description: Optional[str] = None
    scopes: list[str]
    allowed_grant_types: list[str]

