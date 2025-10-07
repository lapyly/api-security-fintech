from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlmodel import SQLModel

from ..domain.models import Transaction


DATABASE_URL = os.getenv(
    "TRANSACTION_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/transactions",
)


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"ssl": "require"},
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_transactions(self) -> list[Transaction]:
        result = await self.session.execute(select(Transaction))
        return list(result.scalars().all())

    async def list_for_account(self, account_id: int) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.account_id == account_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        return await self.session.get(Transaction, transaction_id)

    async def create(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def update(self, transaction: Transaction, *, data: dict) -> Transaction:
        for key, value in data.items():
            setattr(transaction, key, value)
        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction


__all__ = [
    "TransactionRepository",
    "engine",
    "async_session_factory",
    "get_session",
    "init_models",
]

