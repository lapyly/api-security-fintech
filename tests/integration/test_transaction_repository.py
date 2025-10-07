from __future__ import annotations

import importlib
import os

import pytest
from sqlalchemy import text
from testcontainers.postgres import PostgresContainer

from services.transaction_service.domain.models import Transaction
from services.transaction_service.infrastructure import repositories


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_repository_crud_flow() -> None:
    with PostgresContainer("postgres:15-alpine") as postgres:
        sync_url = postgres.get_connection_url()
        async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://")
        os.environ["TRANSACTION_DATABASE_URL"] = async_url
        os.environ["TRANSACTION_DATABASE_SSLMODE"] = "disable"

        repo_module = importlib.reload(repositories)

        async with repo_module.engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: sync_conn.execute(text("CREATE TABLE accounts (id SERIAL PRIMARY KEY)"))
            )
            await conn.run_sync(
                lambda sync_conn: sync_conn.execute(text("CREATE TABLE users (id SERIAL PRIMARY KEY)"))
            )
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("INSERT INTO accounts DEFAULT VALUES")))
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("INSERT INTO users DEFAULT VALUES")))

        await repo_module.init_models()

        async with repo_module.get_session() as session:
            repository = repo_module.TransactionRepository(session)
            created = await repository.create(
                Transaction(
                    account_id=1,
                    user_id=1,
                    amount=49.99,
                    currency="USD",
                    direction="debit",
                    description="Card 4242424242424242",
                    status="pending",
                )
            )

            assert created.id is not None
            assert created.status == "pending"

            fetched = await repository.get_by_id(created.id)
            assert fetched is not None
            assert fetched.description.endswith("4242")

            await repository.update(created, data={"status": "completed"})

            account_transactions = await repository.list_for_account(1)
            assert len(account_transactions) == 1
            assert account_transactions[0].status == "completed"

            all_transactions = await repository.list_transactions()
            assert len(all_transactions) == 1
