from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter

from ..application.schemas import AccountCreate, AccountRead, AccountUpdate
from ..application.services import AccountService
from ..infrastructure.repositories import AccountRepository, UserRepository, get_session
from .dependencies import Principal, require_scopes, sanitize_account, sanitize_accounts


router = APIRouter(prefix="/accounts", tags=["accounts"])


async def get_account_service() -> AsyncIterator[AccountService]:
    async with get_session() as session:
        account_repository = AccountRepository(session)
        user_repository = UserRepository(session)
        service = AccountService(account_repository, user_repository)
        yield service


@router.get(
    "",
    response_model=list[AccountRead],
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def list_accounts(
    account_service: AccountService = Depends(get_account_service),
    _principal: Principal = Depends(require_scopes("accounts:read")),
) -> list[AccountRead]:
    accounts = await account_service.list_accounts()
    return sanitize_accounts(accounts)


@router.post(
    "",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def create_account(
    payload: AccountCreate,
    account_service: AccountService = Depends(get_account_service),
    _principal: Principal = Depends(require_scopes("accounts:write")),
) -> AccountRead:
    try:
        account = await account_service.create_account(payload)
        return sanitize_account(account)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/{account_id}",
    response_model=AccountRead,
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def get_account(
    account_id: int,
    account_service: AccountService = Depends(get_account_service),
    _principal: Principal = Depends(require_scopes("accounts:read")),
) -> AccountRead:
    account = await account_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return sanitize_account(account)


@router.put(
    "/{account_id}",
    response_model=AccountRead,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def update_account(
    account_id: int,
    payload: AccountUpdate,
    account_service: AccountService = Depends(get_account_service),
    _principal: Principal = Depends(require_scopes("accounts:write")),
) -> AccountRead:
    account = await account_service.update_account(account_id, payload)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return sanitize_account(account)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def delete_account(
    account_id: int,
    account_service: AccountService = Depends(get_account_service),
    _principal: Principal = Depends(require_scopes("accounts:write")),
) -> None:
    deleted = await account_service.delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

