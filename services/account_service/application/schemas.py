from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str
    full_name: str


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserRead(UserBase):
    id: int
    created_at: datetime


class AccountBase(BaseModel):
    account_number: str
    account_type: str
    currency: str = "USD"
    status: str = "active"


class AccountCreate(AccountBase):
    user_id: int
    initial_deposit: float = 0.0


class AccountUpdate(BaseModel):
    account_type: Optional[str] = None
    status: Optional[str] = None


class AccountRead(AccountBase):
    id: int
    user_id: int
    balance: float
    created_at: datetime
    updated_at: datetime


class UserWithAccounts(UserRead):
    accounts: list[AccountRead] = Field(default_factory=list)


