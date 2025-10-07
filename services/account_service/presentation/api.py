from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status

from ..application.schemas import AccountCreate, AccountRead, AccountUpdate
from ..application.services import AccountService
from ..infrastructure.repositories import AccountRepository, UserRepository, get_session


router = APIRouter(prefix="/accounts", tags=["accounts"])


async def get_account_service() -> AsyncIterator[AccountService]:
    async with get_session() as session:
        account_repository = AccountRepository(session)
        user_repository = UserRepository(session)
        service = AccountService(account_repository, user_repository)
        yield service


@router.get("", response_model=list[AccountRead])
async def list_accounts(account_service: AccountService = Depends(get_account_service)) -> list[AccountRead]:
    return await account_service.list_accounts()


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountRead:
    try:
        return await account_service.create_account(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(
    account_id: int,
    account_service: AccountService = Depends(get_account_service),
) -> AccountRead:
    account = await account_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: int,
    payload: AccountUpdate,
    account_service: AccountService = Depends(get_account_service),
) -> AccountRead:
    account = await account_service.update_account(account_id, payload)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    account_service: AccountService = Depends(get_account_service),
) -> None:
    deleted = await account_service.delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

