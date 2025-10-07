from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter

from ..application.schemas import TransactionCreate, TransactionRead, TransactionUpdate
from ..application.services import TransactionService
from ..infrastructure.repositories import TransactionRepository, get_session
from .dependencies import (
    Principal,
    require_roles,
    require_scopes,
    sanitize_transaction,
    sanitize_transactions,
)


router = APIRouter(prefix="/transactions", tags=["transactions"])


async def get_transaction_service() -> AsyncIterator[TransactionService]:
    async with get_session() as session:
        repository = TransactionRepository(session)
        service = TransactionService(repository)
        yield service


@router.get(
    "",
    response_model=list[TransactionRead],
    dependencies=[Depends(RateLimiter(times=50, seconds=60))],
)
async def list_transactions(
    service: TransactionService = Depends(get_transaction_service),
    _principal: Principal = Depends(require_scopes("transactions:read")),
) -> list[TransactionRead]:
    transactions = await service.list_transactions()
    return sanitize_transactions(transactions)


@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))],
)
async def create_transaction(
    payload: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    _principal: Principal = Depends(require_scopes("transactions:write")),
    _role_guard: Principal = Depends(require_roles("payments", "risk")),
) -> TransactionRead:
    transaction = await service.create_transaction(payload)
    return sanitize_transaction(transaction)


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    dependencies=[Depends(RateLimiter(times=50, seconds=60))],
)
async def get_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
    _principal: Principal = Depends(require_scopes("transactions:read")),
) -> TransactionRead:
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return sanitize_transaction(transaction)


@router.get(
    "/accounts/{account_id}",
    response_model=list[TransactionRead],
    dependencies=[Depends(RateLimiter(times=30, seconds=60))],
)
async def list_account_transactions(
    account_id: int,
    service: TransactionService = Depends(get_transaction_service),
    _principal: Principal = Depends(require_scopes("transactions:read")),
) -> list[TransactionRead]:
    transactions = await service.list_account_transactions(account_id)
    return sanitize_transactions(transactions)


@router.put(
    "/{transaction_id}",
    response_model=TransactionRead,
    dependencies=[Depends(RateLimiter(times=15, seconds=60))],
)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
    _principal: Principal = Depends(require_scopes("transactions:write")),
    _role_guard: Principal = Depends(require_roles("payments", "risk")),
) -> TransactionRead:
    transaction = await service.update_transaction(transaction_id, payload)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return sanitize_transaction(transaction)

