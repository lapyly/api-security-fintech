from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ..application.schemas import (
    ClientRegistration,
    OAuthClient,
    RefreshTokenRequest,
    TokenRequestMeta,
    TokenResponse,
    TokenRevocationRequest,
)
from ..application.services import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service() -> AuthService:
    demo_clients = [
        OAuthClient(
            client_id="web-portal",
            client_name="Retail Web Portal",
            description="First-party web experience",
            scopes=["accounts:read", "transactions:read"],
            allowed_grant_types=["password", "client_credentials"],
        ),
        OAuthClient(
            client_id="payments-gateway",
            client_name="Payments Gateway",
            description="Handles card transactions for merchant partners",
            scopes=["transactions:write"],
            allowed_grant_types=["client_credentials"],
        ),
    ]
    return AuthService(clients=demo_clients)


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    meta = TokenRequestMeta(
        client_id=form_data.client_id or form_data.username,
        grant_type=form_data.grant_type,
        requested_scope=form_data.scopes_str or None,
        audience=None,
    )
    return service.generate_token(meta)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return service.refresh_token(request)


@router.post("/revoke")
async def revoke_token(
    request: TokenRevocationRequest,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    return service.revoke_token(request.token)


@router.get("/clients", response_model=list[ClientRegistration])
async def list_clients(
    service: AuthService = Depends(get_auth_service),
) -> list[ClientRegistration]:
    return service.list_clients()

