from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, status

router = APIRouter()

_alert_logger = logging.getLogger("alerts.webhook")


@router.post(
    "/alerts",
    status_code=status.HTTP_202_ACCEPTED,
)
async def receive_alert(payload: dict[str, Any]) -> dict[str, str]:
    alerts = payload.get("alerts", [])
    _alert_logger.warning(
        "alert_notification",
        extra={
            "alert_count": len(alerts),
            "compliance": {"regimes": ["soc2", "pci_dss"]},
        },
    )
    return {"status": "received"}
