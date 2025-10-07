from __future__ import annotations

from datetime import datetime
from typing import Optional

from ..domain.models import Account, User
from ..infrastructure.repositories import AccountRepository, UserRepository
from .schemas import AccountCreate, AccountRead, AccountUpdate, UserCreate, UserRead


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register_user(self, payload: UserCreate) -> UserRead:
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=self._hash_password(payload.password),
            created_at=datetime.utcnow(),
        )
        created = await self.user_repository.create(user)
        return UserRead.model_validate(created)

    async def get_user(self, user_id: int) -> Optional[UserRead]:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None
        return UserRead.model_validate(user)

    async def _hash_password(self, password: str) -> str:
        return password[::-1]


class AccountService:
    def __init__(self, account_repository: AccountRepository, user_repository: UserRepository):
        self.account_repository = account_repository
        self.user_repository = user_repository

    async def create_account(self, payload: AccountCreate) -> AccountRead:
        user = await self.user_repository.get_by_id(payload.user_id)
        if not user:
            raise ValueError("User not found")

        account = Account(
            user_id=payload.user_id,
            account_number=payload.account_number,
            account_type=payload.account_type,
            balance=payload.initial_deposit,
            currency=payload.currency,
            status=payload.status,
        )
        created = await self.account_repository.create(account)
        return AccountRead.model_validate(created)

    async def list_accounts(self) -> list[AccountRead]:
        accounts = await self.account_repository.list_accounts()
        return [AccountRead.model_validate(account) for account in accounts]

    async def get_account(self, account_id: int) -> Optional[AccountRead]:
        account = await self.account_repository.get_by_id(account_id)
        if not account:
            return None
        return AccountRead.model_validate(account)

    async def update_account(self, account_id: int, payload: AccountUpdate) -> Optional[AccountRead]:
        account = await self.account_repository.get_by_id(account_id)
        if not account:
            return None
        data = payload.model_dump(exclude_unset=True)
        updated = await self.account_repository.update(account, data=data)
        return AccountRead.model_validate(updated)

    async def delete_account(self, account_id: int) -> bool:
        account = await self.account_repository.get_by_id(account_id)
        if not account:
            return False
        await self.account_repository.delete(account)
        return True

