from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping, Any
from uuid import uuid4


class AuditEventCategory(str, Enum):
    SECURITY = "security"
    TRANSACTION = "transaction"
    COMPLIANCE = "compliance"
    PLATFORM = "platform"


@dataclass(slots=True, frozen=True)
class AuditEvent:
    id: str
    category: AuditEventCategory
    action: str
    actor: str
    principal: str | None
    resource: str | None
    severity: str
    source_service: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    compliance_tags: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        *,
        category: AuditEventCategory,
        action: str,
        actor: str,
        principal: str | None,
        resource: str | None,
        severity: str,
        source_service: str,
        metadata: Mapping[str, Any] | None = None,
        compliance_tags: list[str] | tuple[str, ...] | None = None,
    ) -> "AuditEvent":
        return cls(
            id=str(uuid4()),
            category=category,
            action=action,
            actor=actor,
            principal=principal,
            resource=resource,
            severity=severity,
            source_service=source_service,
            metadata=dict(metadata or {}),
            compliance_tags=tuple(compliance_tags or ()),
        )
