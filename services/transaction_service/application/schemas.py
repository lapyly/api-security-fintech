from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TransactionBase(BaseModel):
    account_id: int
    amount: float
    currency: str = "USD"
    direction: str
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    user_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None


class TransactionRead(TransactionBase):
    id: int
    user_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime


