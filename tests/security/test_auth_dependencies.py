from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import HTTPException

from services.transaction_service.application.schemas import TransactionRead
from services.transaction_service.domain.models import Transaction
from services.transaction_service.presentation.dependencies import (
    Principal,
    require_roles,
    require_scopes,
    sanitize_transaction,
)


@pytest.mark.security
@pytest.mark.asyncio
async def test_require_scopes_allows_authorized_request(principal_factory) -> None:
    dependency = require_scopes("transactions:write", "transactions:read")
    principal = await dependency(principal=principal_factory())
    assert isinstance(principal, Principal)
    assert {"transactions:write", "transactions:read"}.issubset(principal.scopes)


@pytest.mark.security
@pytest.mark.asyncio
async def test_require_scopes_blocks_missing_scope(principal_factory) -> None:
    dependency = require_scopes("accounts:write")
    with pytest.raises(HTTPException) as excinfo:
        await dependency(principal=principal_factory(scopes={"accounts:read"}))
    assert excinfo.value.status_code == 403
    assert "Insufficient scopes" in excinfo.value.detail


@pytest.mark.security
@pytest.mark.asyncio
async def test_require_roles_validates_allowed_role(principal_factory) -> None:
    dependency = require_roles("payments")
    principal = await dependency(principal=principal_factory())
    assert "payments" in principal.roles


@pytest.mark.security
@pytest.mark.asyncio
async def test_require_roles_blocks_unauthorized_role(principal_factory) -> None:
    dependency = require_roles("risk")
    with pytest.raises(HTTPException) as excinfo:
        await dependency(principal=principal_factory(roles={"auditor"}))
    assert excinfo.value.status_code == 403
    assert "Insufficient role" in excinfo.value.detail


@pytest.mark.security
def test_sanitize_transaction_masks_pan_values() -> None:
    transaction = Transaction(
        id=1,
        account_id=123,
        user_id=555,
        amount=10.0,
        currency="USD",
        direction="debit",
        description="Card 4111111111111111 used",
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Pydantic v2 requires validating from either a dict or the originating model.
    transaction_read = TransactionRead.model_validate(transaction)

    sanitized = sanitize_transaction(transaction_read)

    assert sanitized.description.endswith("1111 used")
    assert "411111" not in sanitized.description
