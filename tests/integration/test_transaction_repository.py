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
    # Explicit credentials prevent a mismatch between the async engine and the
    # Postgres container.  Older testcontainers releases boot with the
    # hard-coded ``test``/``test`` combination while newer releases default to
    # ``postgres``/``postgres``.  Pinning the desired values ahead of time keeps
    # both sides aligned regardless of the library version under test.
    requested_credentials = {
        "POSTGRES_USER": "integration_user",
        "POSTGRES_PASSWORD": "integration_password",
        "POSTGRES_DB": "integration_db",
    }

    postgres = PostgresContainer("postgres:15-alpine")
    for key, value in requested_credentials.items():
        # ``with_env`` works across testcontainers v2/v3 and ensures that the
        # container starts with the exact credentials our test expects instead of
        # relying on library defaults that may oscillate between ``test`` and
        # ``postgres`` across releases.
        postgres.with_env(key, value)

    with postgres as container:
        sync_url = make_url(container.get_connection_url())
        credentials = {
            "POSTGRES_USER": sync_url.username or requested_credentials["POSTGRES_USER"],
            "POSTGRES_PASSWORD": sync_url.password or requested_credentials["POSTGRES_PASSWORD"],
            "POSTGRES_DB": sync_url.database or requested_credentials["POSTGRES_DB"],
        }

        # ``PostgresContainer`` may override our requested credentials depending on
        # the library version.  Logging the derived values makes it easier to
        # debug authentication mismatches in CI should they ever resurface.
        print(
            "Using Postgres container credentials:",
            {key: ("***" if key == "POSTGRES_PASSWORD" else value) for key, value in credentials.items()},
        )

        async_url = sync_url.set(drivername="postgresql+asyncpg")
        async_url = async_url.set(username=credentials["POSTGRES_USER"], password=credentials["POSTGRES_PASSWORD"])
        os.environ["TRANSACTION_DATABASE_URL"] = str(async_url)
        os.environ["TRANSACTION_DATABASE_SSLMODE"] = "disable"

        # Surface the normalized credentials for any code path that reads the
        # standard Postgres environment variables during the test run.  The
        # environment variables are kept in sync with the container's real
        # configuration so that asyncpg and SQLAlchemy always authenticate with
        # matching values.
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
