from __future__ import annotations

import importlib
import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from testcontainers.postgres import PostgresContainer

from services.transaction_service.domain.models import Transaction
from services.transaction_service.infrastructure import repositories


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_repository_crud_flow() -> None:
    # Use the same credentials as docker-compose to avoid password mismatches when the
    # repository reads TRANSACTION_DATABASE_URL.  Testcontainers defaults to the
    # ``test`` user/password in v3+, so we explicitly override them via ``env`` to keep
    # compatibility with asyncpg + SQLAlchemy 2.x on Python 3.11.
    credentials = {
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "postgres",
        "POSTGRES_DB": "postgres",
    }
    with PostgresContainer("postgres:15-alpine", env=credentials) as postgres:
        sync_url = make_url(postgres.get_connection_url())
        async_url = sync_url.set(drivername="postgresql+asyncpg")
        os.environ["TRANSACTION_DATABASE_URL"] = str(async_url)
        os.environ["TRANSACTION_DATABASE_SSLMODE"] = "disable"

        # Surface the normalized credentials for any code path that reads the
        # standard Postgres environment variables during the test run.  We reuse
        # the local ``credentials`` mapping to align with testcontainers-postgres
        # 3.x's ``env`` handling while keeping the async configuration intact.
        os.environ["POSTGRES_USER"] = credentials["POSTGRES_USER"]
        os.environ["POSTGRES_PASSWORD"] = credentials["POSTGRES_PASSWORD"]
        os.environ["POSTGRES_DB"] = credentials["POSTGRES_DB"]

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
