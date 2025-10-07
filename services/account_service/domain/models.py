from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(
        index=True,
        nullable=False,
        sa_column_kwargs={"unique": True},
    )
    full_name: str = Field(nullable=False)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    accounts: List["Account"] = Relationship(back_populates="owner")


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    account_number: str = Field(
        index=True,
        nullable=False,
        sa_column_kwargs={"unique": True},
    )
    account_type: str = Field(nullable=False)
    balance: float = Field(default=0.0, nullable=False)
    currency: str = Field(default="USD", nullable=False)
    status: str = Field(default="active", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    owner: Optional[User] = Relationship(back_populates="accounts")


__all__ = ["User", "Account"]

