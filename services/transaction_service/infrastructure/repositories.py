from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlmodel import SQLModel

from ..domain.models import Transaction


DEFAULT_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/transactions"
DATABASE_URL = os.getenv("TRANSACTION_DATABASE_URL", DEFAULT_DATABASE_URL)


def _database_url_from_env() -> str:
    """Return the configured database URL, falling back to the default."""

    return os.getenv("TRANSACTION_DATABASE_URL", DEFAULT_DATABASE_URL)


def _normalize_database_url(url: str) -> str:
    """Ensure the SQLAlchemy URL uses the asyncpg driver."""
    url_obj = make_url(url)
    if "asyncpg" not in url_obj.drivername:
        url_obj = url_obj.set(drivername="postgresql+asyncpg")
    return str(url_obj)


def _connect_args() -> dict[str, object]:
    ssl_mode = os.getenv("TRANSACTION_DATABASE_SSLMODE", "require").lower()
    if ssl_mode in {"disable", "disabled", "off", "false", "0"}:
        return {}
    if ssl_mode in {"require", "true", "on", "1"}:
        return {"ssl": True}
    raise RuntimeError(f"Unsupported TRANSACTION_DATABASE_SSLMODE value: {ssl_mode}")


def _create_engine(url: str) -> AsyncEngine:
    return create_async_engine(
        _normalize_database_url(url),
        echo=False,
        connect_args=_connect_args(),
    )


def _build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def configure_engine(url: str | None = None) -> None:
    """(Re)initialize the async engine and session factory.

    Tests override database credentials at runtime, so the repository needs to
    rebuild its engine after environment variables change.  Reconfiguring the
    engine ensures that integration tests can connect to the ephemeral Postgres
    container started by testcontainers instead of the docker-compose database
    used in local development.
    """

    database_url = url or _database_url_from_env()
    new_engine = _create_engine(database_url)
    new_session_factory = _build_session_factory(new_engine)

    old_engine = globals().get("engine")
    globals()["engine"] = new_engine
    globals()["async_session_factory"] = new_session_factory

    if isinstance(old_engine, AsyncEngine):
        # Disposing the underlying sync engine releases any pooled connections
        # without requiring an async context.
        old_engine.sync_engine.dispose()


configure_engine()


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
    "configure_engine",
]

