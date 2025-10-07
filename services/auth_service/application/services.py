from datetime import datetime, timedelta
from secrets import token_urlsafe
from typing import Iterable

from ..application.schemas import (
    ClientRegistration,
    OAuthClient,
    RefreshTokenRequest,
    TokenRequestMeta,
    TokenResponse,
)


class AuthService:
    """Business use cases supporting OAuth2 token workflows."""

    def __init__(self, clients: Iterable[OAuthClient]):
        self._clients = {client.client_id: client for client in clients}

    def generate_token(self, meta: TokenRequestMeta) -> TokenResponse:
        expires_in = 3600
        access_token = token_urlsafe(32)
        refresh_token = token_urlsafe(48)
        issued_at = datetime.utcnow()
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            issued_at=issued_at,
            scope=meta.requested_scope,
        )

    def refresh_token(self, request: RefreshTokenRequest) -> TokenResponse:
        expires_in = request.expires_in or 3600
        issued_at = datetime.utcnow()
        return TokenResponse(
            access_token=token_urlsafe(32),
            refresh_token=token_urlsafe(48),
            expires_in=expires_in,
            issued_at=issued_at,
            scope=request.scope,
        )

    def revoke_token(self, token: str) -> dict[str, str]:
        return {"status": "revoked", "token": token}

    def list_clients(self) -> list[ClientRegistration]:
        now = datetime.utcnow()
        return [
            ClientRegistration(
                client_id=client.client_id,
                client_name=client.client_name,
                scopes=client.scopes,
                created_at=now,
            )
            for client in self._clients.values()
        ]

