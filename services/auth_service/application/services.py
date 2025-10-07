from datetime import datetime
from typing import Iterable

from ..application.schemas import (
    ClientRegistration,
    OAuthClient,
    RefreshTokenRequest,
    TokenRequestMeta,
    TokenResponse,
)
from .security import JWTService


class AuthService:
    """Business use cases supporting OAuth2 token workflows."""

    def __init__(self, clients: Iterable[OAuthClient], security: JWTService):
        self._clients = {client.client_id: client for client in clients}
        self._security = security

    def _get_client(self, client_id: str | None) -> OAuthClient:
        if not client_id or client_id not in self._clients:
            raise ValueError("Unknown client")
        return self._clients[client_id]

    def generate_token(self, meta: TokenRequestMeta) -> TokenResponse:
        client = self._get_client(meta.client_id)
        requested_scopes = (
            set(meta.requested_scope.split())
            if meta.requested_scope
            else set(client.scopes)
        )
        if not requested_scopes.issubset(set(client.scopes)):
            raise ValueError("Requested scope exceeds client grants")
        if meta.grant_type not in client.allowed_grant_types:
            raise ValueError("Unsupported grant type for client")

        subject = meta.subject or client.client_id
        token_bundle = self._security.issue_tokens(
            subject=subject,
            client_id=client.client_id,
            scopes=requested_scopes,
            roles=client.roles,
            audience=meta.audience,
        )
        return TokenResponse(**token_bundle)

    def refresh_token(self, request: RefreshTokenRequest) -> TokenResponse:
        token_bundle = self._security.rotate_refresh_token(
            request.refresh_token,
            scope=request.scope,
            expires_in=request.expires_in,
        )
        return TokenResponse(**token_bundle)

    def revoke_token(self, token: str) -> dict[str, str]:
        self._security.revoke_refresh_token(token)
        return {"status": "revoked", "token": token}

    def list_clients(self) -> list[ClientRegistration]:
        now = datetime.utcnow()
        return [
            ClientRegistration(
                client_id=client.client_id,
                client_name=client.client_name,
                scopes=client.scopes,
                roles=client.roles,
                created_at=now,
            )
            for client in self._clients.values()
        ]
