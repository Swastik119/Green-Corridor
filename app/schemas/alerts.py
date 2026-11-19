"""
Phase 9 - Persistent Alerts and SMS Notification Schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class MissionAlertCreate(BaseModel):
    """
    Schema for creating a persistent mission alert.
    """
    mission_id: str = Field(..., description="Target mission identifier (e.g. GC-2024-001)")
    ambulance_id: Optional[str] = Field(None, description="Ambulance identifier if vehicle-specific")
    alert_type: str = Field(
        ...,
        description="Category: AMBULANCE_DISCONNECTED, GPS_GAP_DETECTED, ROUTE_DEVIATION, DELAY_WARNING, CRITICAL_STATUS_CHANGE"
    )
    severity: Literal["info", "warning", "critical"] = Field(
        "warning",
        description="Alert severity level: info, warning, critical"
    )
    message: str = Field(..., min_length=5, description="Descriptive alert text")
    details: Optional[dict] = Field(default_factory=dict, description="Supporting telemetry or diagnostic payload")


class MissionAlertResponse(BaseModel):
    """
    Schema for an alert record retrieved from persistence.
    """
    id: str
    mission_id: str
    ambulance_id: Optional[str] = None
    alert_type: str
    severity: str
    message: str
    status: Literal["unread", "acknowledged", "resolved"]
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    details: dict = Field(default_factory=dict)
    sms_sent: bool = False
    sms_sid: Optional[str] = None


class AlertStatusUpdate(BaseModel):
    """
    Schema for updating alert lifecycle status.
    """
    status: Literal["acknowledged", "resolved"]
    actor: Optional[str] = Field("Operator", description="User or officer executing the action")
    remarks: Optional[str] = Field(None, description="Optional resolution note")


class SMSNotificationRequest(BaseModel):
    """
    Schema for manual or simulated SMS alert dispatch.
    """
    phone_number: str = Field(..., description="E.164 formatted recipient phone number")
    message: str = Field(..., min_length=5, max_length=160, description="SMS message content")
    mission_id: Optional[str] = Field(None, description="Associated mission identifier")
    alert_type: Optional[str] = Field("CRITICAL_ALERT", description="Alert trigger category")


class SMSNotificationResponse(BaseModel):
    """
    Response schema for SMS dispatch attempt.
    """
    status: str
    message_sid: str
    recipient: str
    is_mock: bool
    dispatched_at: datetime
    delivery_status: str
