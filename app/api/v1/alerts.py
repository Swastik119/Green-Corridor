"""
Phase 9 - Persistent Alerts & SMS REST API Endpoints.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query

from app.schemas.alerts import (
    MissionAlertCreate,
    MissionAlertResponse,
    AlertStatusUpdate,
    SMSNotificationRequest,
    SMSNotificationResponse,
)
from app.services.alert_service import alert_service
from app.services.sms_service import sms_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["Persistent Alerts & Emergency SMS"])


@router.get(
    "/",
    response_model=List[MissionAlertResponse],
    summary="List persistent mission alerts",
)
def list_alerts(
    mission_id: Optional[str] = Query(None, description="Filter by mission ID"),
    status: Optional[str] = Query(None, description="Filter: unread, acknowledged, resolved"),
    severity: Optional[str] = Query(None, description="Filter: info, warning, critical"),
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieves persistent alerts matching criteria in reverse chronological order."""
    return alert_service.get_alerts_for_mission(
        mission_id=mission_id,
        status=status,
        severity=severity,
        limit=limit,
    )


@router.post(
    "/",
    response_model=MissionAlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and broadcast a persistent mission alert",
)
def create_alert(payload: MissionAlertCreate):
    """
    Creates an operational alert, stores it, broadcasts it via WebSocket,
    and automatically triggers SMS fallback if severity is critical.
    """
    alert = alert_service.create_alert(payload)
    return alert


@router.put(
    "/{alert_id}/acknowledge",
    response_model=MissionAlertResponse,
    summary="Acknowledge a mission alert",
)
def acknowledge_alert(alert_id: str, payload: AlertStatusUpdate):
    """Marks an alert as acknowledged by an operator or authority."""
    updated = alert_service.acknowledge_alert(
        alert_id=alert_id,
        actor=payload.actor or "Operator",
        remarks=payload.remarks,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated


@router.put(
    "/{alert_id}/resolve",
    response_model=MissionAlertResponse,
    summary="Resolve a mission alert",
)
def resolve_alert(alert_id: str, payload: AlertStatusUpdate):
    """Marks an alert as resolved."""
    updated = alert_service.resolve_alert(
        alert_id=alert_id,
        actor=payload.actor or "Operator",
        remarks=payload.remarks,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated


@router.post(
    "/sms",
    response_model=SMSNotificationResponse,
    summary="Dispatch an emergency SMS notification (Live or Mock)",
)
def dispatch_sms(payload: SMSNotificationRequest):
    """
    Dispatches an emergency SMS. Automatically executes in mock delivery mode
    if external credentials are not set, guaranteeing zero downtime.
    """
    result = sms_service.send_alert_sms(
        recipient_phone=payload.phone_number,
        message_text=payload.message,
        mission_id=payload.mission_id,
        alert_type=payload.alert_type,
    )
    return SMSNotificationResponse(**result)


@router.get(
    "/sms/audit",
    summary="Get recent SMS dispatch audit records",
)
def get_sms_audit(limit: int = Query(25, ge=1, le=100)):
    """Retrieves the recent SMS dispatch log."""
    return {
        "status": "success",
        "total": len(sms_service.get_audit_log(limit)),
        "records": sms_service.get_audit_log(limit),
    }
