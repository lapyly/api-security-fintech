from __future__ import annotations

from datetime import datetime

import pytest

from services.transaction_service.application.schemas import (
    TransactionCreate,
    TransactionUpdate,
)
from services.transaction_service.application.services import TransactionService
from services.transaction_service.domain.models import Transaction


class FakeTransactionRepository:
    def __init__(self) -> None:
        self._items: dict[int, Transaction] = {}
        self._pk = 0

    async def list_transactions(self) -> list[Transaction]:
        return list(self._items.values())

    async def list_for_account(self, account_id: int) -> list[Transaction]:
        return [tx for tx in self._items.values() if tx.account_id == account_id]

    async def get_by_id(self, transaction_id: int) -> Transaction | None:
        return self._items.get(transaction_id)

    async def create(self, transaction: Transaction) -> Transaction:
        self._pk += 1
        transaction.id = self._pk
        transaction.created_at = datetime.utcnow()
        transaction.updated_at = transaction.created_at
        self._items[self._pk] = transaction
        return transaction

    async def update(self, transaction: Transaction, *, data: dict) -> Transaction:
        for key, value in data.items():
            setattr(transaction, key, value)
        transaction.updated_at = datetime.utcnow()
        self._items[transaction.id] = transaction
        return transaction


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_transaction_defaults() -> None:
    repository = FakeTransactionRepository()
    service = TransactionService(repository)

    payload = TransactionCreate(
        account_id=200,
        user_id=300,
        amount=99.45,
        currency="EUR",
        direction="debit",
        description="Invoice 001",
    )

    created = await service.create_transaction(payload)

    assert created.id == 1
    assert created.status == "pending"
    assert created.currency == "EUR"
    assert created.account_id == 200
    assert created.user_id == 300


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_transaction_status_change() -> None:
    repository = FakeTransactionRepository()
    service = TransactionService(repository)

    created = await service.create_transaction(
        TransactionCreate(
            account_id=200,
            user_id=None,
            amount=50,
            currency="USD",
            direction="credit",
            description="Manual adjustment",
        )
    )

    updated = await service.update_transaction(
        created.id,
        TransactionUpdate(status="completed"),
    )

    assert updated is not None
    assert updated.status == "completed"
    assert updated.description == "Manual adjustment"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_account_transactions_filters_only_matching_account() -> None:
    repository = FakeTransactionRepository()
    service = TransactionService(repository)

    await service.create_transaction(
        TransactionCreate(
            account_id=1,
            user_id=None,
            amount=10,
            currency="USD",
            direction="debit",
            description="Coffee",
        )
    )
    await service.create_transaction(
        TransactionCreate(
            account_id=2,
            user_id=None,
            amount=200,
            currency="USD",
            direction="credit",
            description="Payroll",
        )
    )

    results = await service.list_account_transactions(2)

    assert len(results) == 1
    assert results[0].account_id == 2
    assert results[0].amount == 200
