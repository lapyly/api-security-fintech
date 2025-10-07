"""JWT utilities and refresh token management for the auth service."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import token_urlsafe
from typing import Any, Dict, Iterable, Optional

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import serialization


@dataclass(slots=True)
class JWTSettings:
    """Configuration required to issue and verify JSON Web Tokens."""

    issuer: str
    audience: Optional[str]
    private_key: str
    public_key: str
    key_id: str = "auth-service-key"
    access_token_ttl: timedelta = timedelta(minutes=15)
    refresh_token_ttl: timedelta = timedelta(days=7)

    @classmethod
    def from_env(cls) -> "JWTSettings":
        """Build settings by loading key material from disk via env vars."""

        issuer = os.getenv("AUTH_JWT_ISSUER", "https://auth-service.local")
        audience = os.getenv("AUTH_JWT_AUDIENCE")
        private_key_path = Path(
            os.getenv("AUTH_PRIVATE_KEY_PATH", "/certs/auth_service.key")
        )
        public_key_path = Path(
            os.getenv("AUTH_PUBLIC_KEY_PATH", "/certs/auth_service.crt")
        )
        key_id = os.getenv("AUTH_JWT_KID", "auth-service-key")
        if not private_key_path.exists():
            raise FileNotFoundError(f"Private key not found at {private_key_path}")
        if not public_key_path.exists():
            raise FileNotFoundError(f"Public key not found at {public_key_path}")

        private_key = private_key_path.read_text()
        public_key = public_key_path.read_text()
        access_minutes = int(os.getenv("AUTH_ACCESS_TOKEN_MINUTES", "15"))
        refresh_days = int(os.getenv("AUTH_REFRESH_TOKEN_DAYS", "7"))
        return cls(
            issuer=issuer,
            audience=audience,
            private_key=private_key,
            public_key=public_key,
            key_id=key_id,
            access_token_ttl=timedelta(minutes=access_minutes),
            refresh_token_ttl=timedelta(days=refresh_days),
        )


@dataclass(slots=True)
class RefreshSession:
    """Metadata about an active refresh token."""

    subject: str
    client_id: str
    scopes: set[str]
    roles: set[str]
    expires_at: datetime

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at


class JWTService:
    """Service responsible for minting JWTs and rotating refresh tokens."""

    def __init__(self, settings: JWTSettings):
        self._settings = settings
        self._refresh_tokens: dict[str, RefreshSession] = {}
        self._public_key_obj = self._load_public_key(settings.public_key)

    @staticmethod
    def _load_public_key(pem_data: str):
        try:
            cert = x509.load_pem_x509_certificate(pem_data.encode("utf-8"))
            return cert.public_key()
        except ValueError:
            return serialization.load_pem_public_key(pem_data.encode("utf-8"))

    @property
    def settings(self) -> JWTSettings:
        return self._settings

    def _hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _register_refresh_token(
        self, token: str, session: RefreshSession
    ) -> None:
        self._refresh_tokens[self._hash_refresh_token(token)] = session

    def _pop_refresh_token(self, token: str) -> RefreshSession:
        hashed = self._hash_refresh_token(token)
        session = self._refresh_tokens.pop(hashed, None)
        if session is None:
            raise ValueError("Invalid refresh token")
        return session

    def issue_tokens(
        self,
        *,
        subject: str,
        client_id: str,
        scopes: Iterable[str],
        roles: Iterable[str],
        audience: Optional[str] = None,
    ) -> dict[str, Any]:
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + self._settings.access_token_ttl
        scope_set = set(scopes)
        roles_set = set(roles)

        payload: Dict[str, Any] = {
            "iss": self._settings.issuer,
            "sub": subject,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
            "scope": " ".join(sorted(scope_set)),
            "client_id": client_id,
            "roles": sorted(roles_set),
        }
        aud_claim = audience or self._settings.audience
        if aud_claim:
            payload["aud"] = aud_claim
        headers = {"kid": self._settings.key_id, "typ": "JWT"}
        access_token = jwt.encode(
            payload,
            self._settings.private_key,
            algorithm="RS256",
            headers=headers,
        )

        refresh_token = token_urlsafe(48)
        refresh_expires = issued_at + self._settings.refresh_token_ttl
        session = RefreshSession(
            subject=subject,
            client_id=client_id,
            scopes=scope_set,
            roles=roles_set,
            expires_at=refresh_expires,
        )
        self._register_refresh_token(refresh_token, session)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": int(self._settings.access_token_ttl.total_seconds()),
            "issued_at": issued_at,
            "scope": " ".join(sorted(scope_set)) or None,
        }

    def rotate_refresh_token(
        self,
        refresh_token: str,
        *,
        scope: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> dict[str, Any]:
        session = self._pop_refresh_token(refresh_token)
        if session.is_expired():
            raise ValueError("Refresh token expired")

        requested_scope = set(scope.split()) if scope else session.scopes
        if not requested_scope.issubset(session.scopes):
            raise ValueError("Requested scope exceeds original grant")

        if expires_in is not None:
            ttl = timedelta(seconds=expires_in)
        else:
            ttl = self._settings.access_token_ttl

        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + ttl
        payload: Dict[str, Any] = {
            "iss": self._settings.issuer,
            "sub": session.subject,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
            "scope": " ".join(sorted(requested_scope)),
            "client_id": session.client_id,
            "roles": sorted(session.roles),
        }
        if self._settings.audience:
            payload["aud"] = self._settings.audience
        headers = {"kid": self._settings.key_id, "typ": "JWT"}
        access_token = jwt.encode(
            payload,
            self._settings.private_key,
            algorithm="RS256",
            headers=headers,
        )

        next_refresh_token = token_urlsafe(48)
        refresh_expires = issued_at + self._settings.refresh_token_ttl
        self._register_refresh_token(
            next_refresh_token,
            RefreshSession(
                subject=session.subject,
                client_id=session.client_id,
                scopes=session.scopes,
                roles=session.roles,
                expires_at=refresh_expires,
            ),
        )

        return {
            "access_token": access_token,
            "refresh_token": next_refresh_token,
            "expires_in": int(ttl.total_seconds()),
            "issued_at": issued_at,
            "scope": " ".join(sorted(requested_scope)) or None,
        }

    def revoke_refresh_token(self, token: str) -> None:
        hashed = self._hash_refresh_token(token)
        self._refresh_tokens.pop(hashed, None)

    def jwks(self) -> dict[str, Any]:
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self._public_key_obj))
        jwk.update({"kid": self._settings.key_id, "use": "sig", "alg": "RS256"})
        return {"keys": [jwk]}


__all__ = ["JWTService", "JWTSettings", "RefreshSession"]
