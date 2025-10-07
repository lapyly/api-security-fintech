from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter

from ..application.schemas import (
    ClientRegistration,
    RefreshTokenRequest,
    TokenRequestMeta,
    TokenResponse,
    TokenRevocationRequest,
)
from ..application.services import AuthService
from .dependencies import decode_bearer_token, get_auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    response_model=TokenResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def issue_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    meta = TokenRequestMeta(
        client_id=form_data.client_id or "web-portal",
        grant_type=form_data.grant_type,
        requested_scope=form_data.scopes_str or None,
        audience=None,
        subject=form_data.username or form_data.client_id,
    )
    try:
        return service.generate_token(meta)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return service.refresh_token(request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/revoke",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def revoke_token(
    request: TokenRevocationRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    service.revoke_token(request.token)
    return {"status": "revoked", "token": request.token}


@router.get("/clients", response_model=list[ClientRegistration])
async def list_clients(
    _: dict = Depends(decode_bearer_token),
    service: AuthService = Depends(get_auth_service),
) -> list[ClientRegistration]:
    return service.list_clients()
