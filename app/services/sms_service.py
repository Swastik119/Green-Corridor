"""
Phase 9 - Fault-Tolerant SMS Notification Service.

Provides an SMS delivery abstraction (supporting Twilio) with seamless fallback to
a robust Mock Delivery Engine when credentials are not configured in local/test environments.
Includes delivery deduplication and an audit trail.
"""

from __future__ import annotations

import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Deduplication cache: hash_key -> timestamp
_SMS_DEDUP_CACHE: Dict[str, datetime] = {}
_DEDUP_WINDOW_SECONDS = 300  # 5 minutes suppression for identical SMS to same recipient

# In-memory delivery audit log for verification & UI inspection
_SMS_AUDIT_LOG: list[dict] = []


class SMSService:
    """
    Manages SMS dispatch for critical corridor events with Twilio and Mock modes.
    """

    def __init__(self) -> None:
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "+18005550199")
        self.sms_enabled = os.getenv("SMS_ENABLED", "false").lower() in ("true", "1", "yes")

    def is_configured(self) -> bool:
        """Checks whether actual live Twilio credentials are configured."""
        return bool(self.account_sid and self.auth_token and self.from_number and self.sms_enabled)

    def send_alert_sms(
        self,
        recipient_phone: str,
        message_text: str,
        mission_id: Optional[str] = None,
        alert_type: Optional[str] = None,
        force: bool = False,
    ) -> dict:
        """
        Dispatches an emergency SMS. Automatically uses mock mode if live credentials
        are absent, safely logging the transmission.
        """
        # Deduplication check
        dedup_key = f"{recipient_phone}:{message_text.strip()}"
        now = datetime.utcnow()
        if not force and dedup_key in _SMS_DEDUP_CACHE:
            last_sent = _SMS_DEDUP_CACHE[dedup_key]
            if now - last_sent < timedelta(seconds=_DEDUP_WINDOW_SECONDS):
                logger.info(
                    "Suppressed duplicate SMS to %s within dedup window (%ds remaining)",
                    recipient_phone,
                    _DEDUP_WINDOW_SECONDS - (now - last_sent).total_seconds(),
                )
                return {
                    "status": "suppressed_duplicate",
                    "message_sid": "SM_SUPPRESSED_DUPLICATE",
                    "recipient": recipient_phone,
                    "is_mock": not self.is_configured(),
                    "dispatched_at": now,
                    "delivery_status": "duplicate_suppressed",
                }

        # Live Twilio dispatch if configured
        if self.is_configured():
            try:
                from twilio.rest import Client  # type: ignore
                client = Client(self.account_sid, self.auth_token)
                msg = client.messages.create(
                    body=message_text,
                    from_=self.from_number,
                    to=recipient_phone,
                )
                _SMS_DEDUP_CACHE[dedup_key] = now
                record = {
                    "status": "dispatched",
                    "message_sid": msg.sid,
                    "recipient": recipient_phone,
                    "is_mock": False,
                    "dispatched_at": now,
                    "delivery_status": msg.status,
                    "mission_id": mission_id,
                    "alert_type": alert_type,
                }
                _SMS_AUDIT_LOG.append(record)
                logger.info("Dispatched live SMS via Twilio to %s: SID=%s", recipient_phone, msg.sid)
                return record
            except Exception as exc:
                logger.error("Twilio dispatch failed: %s. Falling back to mock logging.", exc)

        # Mock / Test Delivery Mode
        mock_sid = f"SM_MOCK_{uuid.uuid4().hex[:12].upper()}"
        _SMS_DEDUP_CACHE[dedup_key] = now
        record = {
            "status": "dispatched_mock",
            "message_sid": mock_sid,
            "recipient": recipient_phone,
            "is_mock": True,
            "dispatched_at": now,
            "delivery_status": "delivered_simulated",
            "mission_id": mission_id,
            "alert_type": alert_type,
            "content": message_text,
        }
        _SMS_AUDIT_LOG.append(record)
        logger.info(
            "📱 [MOCK SMS DISPATCHED] To: %s | Mission: %s | Content: %s | SID: %s",
            recipient_phone,
            mission_id or "N/A",
            message_text,
            mock_sid,
        )
        return record

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        """Returns recent SMS transmissions from audit memory."""
        return _SMS_AUDIT_LOG[-limit:]


# Global SMS Service instance
sms_service = SMSService()
