from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status

from ..application.schemas import TransactionCreate, TransactionRead, TransactionUpdate
from ..application.services import TransactionService
from ..infrastructure.repositories import TransactionRepository, get_session


router = APIRouter(prefix="/transactions", tags=["transactions"])


async def get_transaction_service() -> AsyncIterator[TransactionService]:
    async with get_session() as session:
        repository = TransactionRepository(session)
        service = TransactionService(repository)
        yield service


@router.get("", response_model=list[TransactionRead])
async def list_transactions(
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionRead]:
    return await service.list_transactions()


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    return await service.create_transaction(payload)


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction


@router.get("/accounts/{account_id}", response_model=list[TransactionRead])
async def list_account_transactions(
    account_id: int,
    service: TransactionService = Depends(get_transaction_service),
) -> list[TransactionRead]:
    return await service.list_account_transactions(account_id)


@router.put("/{transaction_id}", response_model=TransactionRead)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    transaction = await service.update_transaction(transaction_id, payload)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction

