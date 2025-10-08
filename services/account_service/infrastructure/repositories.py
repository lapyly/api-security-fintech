from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlmodel import SQLModel

from ..domain.models import Account, User


DATABASE_URL = os.getenv(
    "ACCOUNT_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@db:5432/accounts",
)


def _normalize_database_url(url: str) -> str:
    """Ensure the SQLAlchemy URL uses the asyncpg driver."""
    url_obj = make_url(url)
    if "asyncpg" not in url_obj.drivername:
        url_obj = url_obj.set(drivername="postgresql+asyncpg")
    return str(url_obj)


def _connect_args() -> dict[str, object]:
    ssl_mode = os.getenv("ACCOUNT_DATABASE_SSLMODE", "require").lower()
    if ssl_mode in {"disable", "disabled", "off", "false", "0"}:
        return {}
    if ssl_mode in {"require", "true", "on", "1"}:
        return {"ssl": True}
    raise RuntimeError(f"Unsupported ACCOUNT_DATABASE_SSLMODE value: {ssl_mode}")


engine = create_async_engine(
    _normalize_database_url(DATABASE_URL),
    echo=False,
    connect_args=_connect_args(),
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_users(self) -> list[User]:
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user


class AccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_accounts(self) -> list[Account]:
        result = await self.session.execute(select(Account))
        return list(result.scalars().all())

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        return await self.session.get(Account, account_id)

    async def get_by_number(self, account_number: str) -> Optional[Account]:
        result = await self.session.execute(
            select(Account).where(Account.account_number == account_number)
        )
        return result.scalars().first()

    async def create(self, account: Account) -> Account:
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def update(self, account: Account, *, data: dict) -> Account:
        for key, value in data.items():
            setattr(account, key, value)
        await self.session.commit()
        await self.session.refresh(account)
        return account

    async def delete(self, account: Account) -> None:
        await self.session.delete(account)
        await self.session.commit()


__all__ = [
    "AccountRepository",
    "UserRepository",
    "engine",
    "async_session_factory",
    "get_session",
    "init_models",
]

