from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from pydantic import BaseModel, Field

from ..domain.models import AuditEvent, AuditEventCategory
from ..infrastructure.repository import AuditEventRepository
from .dependencies import (
    get_audit_repository,
    require_mutual_tls_identity,
    require_scopes,
)
from .metrics import record_audit_event

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventPayload(BaseModel):
    category: AuditEventCategory
    action: str = Field(..., min_length=1)
    actor: str = Field(..., min_length=1)
    principal: str | None = Field(default=None)
    resource: str | None = Field(default=None)
    severity: str = Field(default="info")
    metadata: dict[str, Any] = Field(default_factory=dict)
    compliance_tags: list[str] = Field(default_factory=list)


class AuditEventResponse(BaseModel):
    id: str
    created_at: datetime


class AuditEventRead(BaseModel):
    id: str
    category: AuditEventCategory
    action: str
    actor: str
    principal: str | None
    resource: str | None
    severity: str
    source_service: str
    metadata: dict[str, Any]
    compliance_tags: tuple[str, ...]
    created_at: datetime

    @classmethod
    def from_domain(cls, event: AuditEvent) -> "AuditEventRead":
        return cls(
            id=event.id,
            category=event.category,
            action=event.action,
            actor=event.actor,
            principal=event.principal,
            resource=event.resource,
            severity=event.severity,
            source_service=event.source_service,
            metadata=dict(event.metadata),
            compliance_tags=tuple(event.compliance_tags),
            created_at=event.created_at,
        )


@router.post(
    "/events",
    response_model=AuditEventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scopes("audit:write"))],
)
async def record_event(
    payload: AuditEventPayload,
    repository: AuditEventRepository = Depends(get_audit_repository),
    client_cn: str = Depends(require_mutual_tls_identity),
) -> AuditEventResponse:
    event = AuditEvent.create(
        category=payload.category,
        action=payload.action,
        actor=payload.actor,
        principal=payload.principal,
        resource=payload.resource,
        severity=payload.severity,
        source_service=client_cn,
        metadata=payload.metadata,
        compliance_tags=payload.compliance_tags,
    )
    await repository.append(event)
    record_audit_event(event.category.value, event.source_service)
    return AuditEventResponse(id=event.id, created_at=event.created_at)


@router.get(
    "/events",
    response_model=list[AuditEventRead],
    dependencies=[Depends(require_scopes("audit:read"))],
)
async def list_events(
    repository: AuditEventRepository = Depends(get_audit_repository),
    limit: int = 100,
) -> list[AuditEventRead]:
    if limit <= 0 or limit > 500:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="limit must be between 1 and 500")
    events = await repository.list_events(limit)
    return [AuditEventRead.from_domain(event) for event in events]
