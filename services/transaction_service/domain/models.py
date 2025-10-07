from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True, nullable=False)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    amount: float = Field(nullable=False)
    currency: str = Field(default="USD", nullable=False)
    direction: str = Field(default="debit", nullable=False)
    description: Optional[str] = Field(default=None)
    status: str = Field(default="pending", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


__all__ = ["Transaction"]

