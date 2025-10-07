from __future__ import annotations

from typing import Optional

from ..domain.models import Transaction
from ..infrastructure.repositories import TransactionRepository
from .schemas import TransactionCreate, TransactionRead, TransactionUpdate


class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    async def create_transaction(self, payload: TransactionCreate) -> TransactionRead:
        transaction = Transaction(
            account_id=payload.account_id,
            user_id=payload.user_id,
            amount=payload.amount,
            currency=payload.currency,
            direction=payload.direction,
            description=payload.description,
            status="pending",
        )
        created = await self.repository.create(transaction)
        return TransactionRead.model_validate(created)

    async def get_transaction(self, transaction_id: int) -> Optional[TransactionRead]:
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            return None
        return TransactionRead.model_validate(transaction)

    async def list_transactions(self) -> list[TransactionRead]:
        transactions = await self.repository.list_transactions()
        return [TransactionRead.model_validate(tx) for tx in transactions]

    async def list_account_transactions(self, account_id: int) -> list[TransactionRead]:
        transactions = await self.repository.list_for_account(account_id)
        return [TransactionRead.model_validate(tx) for tx in transactions]

    async def update_transaction(
        self, transaction_id: int, payload: TransactionUpdate
    ) -> Optional[TransactionRead]:
        transaction = await self.repository.get_by_id(transaction_id)
        if not transaction:
            return None
        data = payload.model_dump(exclude_unset=True)
        updated = await self.repository.update(transaction, data=data)
        return TransactionRead.model_validate(updated)

