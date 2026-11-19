"""
Phase 9 - Persistent Mission Alert Service.

Stores, manages, and broadcasts critical operational alerts (e.g. GPS gaps,
unauthorized diversions, delay warnings, disconnection alerts) across missions.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict
from collections import OrderedDict

from app.schemas.alerts import MissionAlertCreate, MissionAlertResponse
from app.services.sms_service import sms_service
from app.websocket.manager import tracking_ws_manager

logger = logging.getLogger(__name__)

# Emergency dispatch contacts for critical SMS fallback
EMERGENCY_CONTACTS: Dict[str, str] = {
    "TRAFFIC_HQ": "+91-11-23010101",
    "AMBULANCE_DISPATCH": "+91-98765-43210",
    "CENTRAL_CONTROL": "+91-11-26588500",
}


class AlertService:
    """
    Manages lifecycle of persistent mission alerts.
    """

    def __init__(self) -> None:
        # alert_id -> alert dict
        self._alerts: OrderedDict[str, dict] = OrderedDict()
        self._max_alerts: int = 500

    def create_alert(self, alert_in: MissionAlertCreate) -> dict:
        """
        Creates, persists, broadcasts, and triggers fallback SMS for a new mission alert.
        """
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.utcnow()

        # Deduplication check: prevent identical unread alerts within 60 seconds
        for existing in reversed(self._alerts.values()):
            if (
                existing["mission_id"] == alert_in.mission_id
                and existing["alert_type"] == alert_in.alert_type
                and existing["status"] == "unread"
                and (now - existing["created_at"]).total_seconds() < 60
            ):
                logger.info("Suppressed duplicate alert [%s] for mission [%s]", alert_in.alert_type, alert_in.mission_id)
                return existing

        sms_result = None
        sms_sent = False
        sms_sid = None

        # Critical severity triggers automated SMS fallback
        if alert_in.severity == "critical":
            recipient = EMERGENCY_CONTACTS.get("TRAFFIC_HQ", "+91-98765-43210")
            sms_text = f"🚨 GREEN CORRIDOR CRITICAL [{alert_in.mission_id}]: {alert_in.message[:120]}"
            sms_result = sms_service.send_alert_sms(
                recipient_phone=recipient,
                message_text=sms_text,
                mission_id=alert_in.mission_id,
                alert_type=alert_in.alert_type,
            )
            sms_sent = True
            sms_sid = sms_result.get("message_sid")

        record = {
            "id": alert_id,
            "mission_id": alert_in.mission_id,
            "ambulance_id": alert_in.ambulance_id,
            "alert_type": alert_in.alert_type,
            "severity": alert_in.severity,
            "message": alert_in.message,
            "status": "unread",
            "created_at": now,
            "acknowledged_at": None,
            "acknowledged_by": None,
            "resolved_at": None,
            "resolved_by": None,
            "details": alert_in.details or {},
            "sms_sent": sms_sent,
            "sms_sid": sms_sid,
        }

        self._alerts[alert_id] = record
        if len(self._alerts) > self._max_alerts:
            self._alerts.popitem(last=False)

        logger.info(
            "Created persistent alert [%s] for mission [%s] (Severity: %s)",
            alert_id,
            alert_in.mission_id,
            alert_in.severity,
        )

        # Broadcast asynchronously over WebSocket to all subscribers in this mission room
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(
                tracking_ws_manager.broadcast_to_mission(
                    mission_id=alert_in.mission_id,
                    message_data={
                        "type": "persistent_alert",
                        "data": {
                            **record,
                            "created_at": now.isoformat(),
                        },
                    },
                )
            )
        except RuntimeError:
            pass
        except Exception as ws_err:
            logger.debug("Could not schedule WebSocket alert broadcast: %s", ws_err)

        return record

    def get_alerts_for_mission(
        self,
        mission_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """
        Retrieves matching alerts in reverse chronological order.
        """
        results = []
        for alert in reversed(self._alerts.values()):
            if mission_id and alert["mission_id"] != mission_id:
                continue
            if status and alert["status"] != status:
                continue
            if severity and alert["severity"] != severity:
                continue
            results.append(alert)
            if len(results) >= limit:
                break
        return results

    def acknowledge_alert(self, alert_id: str, actor: str = "Operator", remarks: Optional[str] = None) -> Optional[dict]:
        """Marks alert as acknowledged."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        alert["status"] = "acknowledged"
        alert["acknowledged_at"] = datetime.utcnow()
        alert["acknowledged_by"] = actor
        if remarks:
            alert.setdefault("details", {})["ack_remarks"] = remarks
        logger.info("Alert [%s] acknowledged by %s", alert_id, actor)
        return alert

    def resolve_alert(self, alert_id: str, actor: str = "Operator", remarks: Optional[str] = None) -> Optional[dict]:
        """Marks alert as resolved."""
        alert = self._alerts.get(alert_id)
        if not alert:
            return None
        alert["status"] = "resolved"
        alert["resolved_at"] = datetime.utcnow()
        alert["resolved_by"] = actor
        if remarks:
            alert.setdefault("details", {})["res_remarks"] = remarks
        logger.info("Alert [%s] resolved by %s", alert_id, actor)
        return alert


# Global singleton instance
alert_service = AlertService()
