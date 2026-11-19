"""
Phase 9 Test Suite - Fault-Tolerant Communication, Offline Queuing & Persistent Alerts.
Covers:
  - Batch offline GPS synchronization with idempotency deduplication
  - Persistent alert creation, retrieval, acknowledgement, and resolution
  - Emergency SMS dispatch in mock delivery mode and deduplication suppression
  - WebSocket connection health and ping/pong heartbeat
"""

import unittest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.services.sms_service import sms_service
from app.services.alert_service import alert_service
from app.schemas.alerts import MissionAlertCreate


class TestPhase9FaultTolerance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_offline_gps_batch_sync_and_deduplication(self):
        """
        Tests that queued offline GPS updates are successfully ingested,
        and that duplicate idempotency keys are safely suppressed without error.
        """
        mission_id = f"SYNC-TEST-{uuid.uuid4().hex[:6].upper()}"
        key1 = f"KEY_{uuid.uuid4().hex}"
        key2 = f"KEY_{uuid.uuid4().hex}"

        payload = {
            "mission_id": mission_id,
            "ambulance_id": "AMB-SYNC-01",
            "updates": [
                {
                    "idempotency_key": key1,
                    "latitude": 28.5672,
                    "longitude": 77.2100,
                    "speed": 58.0,
                    "heading": 175.0,
                    "timestamp": "2026-11-19T10:00:00Z",
                    "is_simulated": True,
                },
                {
                    "idempotency_key": key2,
                    "latitude": 28.5600,
                    "longitude": 77.2110,
                    "speed": 62.0,
                    "heading": 178.0,
                    "timestamp": "2026-11-19T10:00:05Z",
                    "is_simulated": True,
                },
            ],
        }

        # First synchronization: both points should be synced
        res1 = self.client.post("/api/v1/tracking/sync", json=payload)
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertEqual(data1["status"], "success")
        self.assertEqual(data1["received_count"], 2)
        self.assertEqual(data1["synced_count"], 2)
        self.assertEqual(data1["duplicates_skipped"], 0)

        # Second synchronization with same payload: both points should be detected as duplicates
        res2 = self.client.post("/api/v1/tracking/sync", json=payload)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["received_count"], 2)
        self.assertEqual(data2["synced_count"], 0)
        self.assertEqual(data2["duplicates_skipped"], 2)

    def test_persistent_alerts_lifecycle(self):
        """
        Tests creating, retrieving, acknowledging, and resolving persistent mission alerts.
        """
        mission_id = f"ALERT-TEST-{uuid.uuid4().hex[:6].upper()}"

        # 1. Create alert
        create_payload = {
            "mission_id": mission_id,
            "alert_type": "GPS_GAP_DETECTED",
            "severity": "warning",
            "message": "Ambulance telemetry silent for 35 seconds.",
            "details": {"gap_seconds": 35.0},
        }
        create_res = self.client.post("/api/v1/alerts/", json=create_payload)
        self.assertEqual(create_res.status_code, 201)
        alert_data = create_res.json()
        alert_id = alert_data["id"]
        self.assertEqual(alert_data["status"], "unread")
        self.assertEqual(alert_data["mission_id"], mission_id)

        # 2. Retrieve alerts by mission
        get_res = self.client.get(f"/api/v1/alerts/?mission_id={mission_id}")
        self.assertEqual(get_res.status_code, 200)
        alerts_list = get_res.json()
        self.assertTrue(any(a["id"] == alert_id for a in alerts_list))

        # 3. Acknowledge alert
        ack_res = self.client.put(
            f"/api/v1/alerts/{alert_id}/acknowledge",
            json={"status": "acknowledged", "actor": "Officer Sharma", "remarks": "Contacted ambulance driver"},
        )
        self.assertEqual(ack_res.status_code, 200)
        ack_data = ack_res.json()
        self.assertEqual(ack_data["status"], "acknowledged")
        self.assertEqual(ack_data["acknowledged_by"], "Officer Sharma")

        # 4. Resolve alert
        res_res = self.client.put(
            f"/api/v1/alerts/{alert_id}/resolve",
            json={"status": "resolved", "actor": "Control Room Lead", "remarks": "Telemetry restored"},
        )
        self.assertEqual(res_res.status_code, 200)
        res_data = res_res.json()
        self.assertEqual(res_data["status"], "resolved")
        self.assertEqual(res_data["resolved_by"], "Control Room Lead")

    def test_sms_fallback_mock_dispatch_and_deduplication(self):
        """
        Tests mock SMS dispatch, deduplication suppression, and audit trail retrieval.
        """
        phone = "+91-98765-43210"
        msg = f"CRITICAL TEST ALERT {uuid.uuid4().hex[:6]}"

        # 1. Dispatch SMS
        res1 = self.client.post(
            "/api/v1/alerts/sms",
            json={"phone_number": phone, "message": msg, "mission_id": "GC-TEST"},
        )
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertTrue(data1["is_mock"])
        self.assertTrue(data1["message_sid"].startswith("SM_MOCK_"))

        # 2. Duplicate dispatch within window should be suppressed
        res2 = self.client.post(
            "/api/v1/alerts/sms",
            json={"phone_number": phone, "message": msg, "mission_id": "GC-TEST"},
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertEqual(data2["delivery_status"], "duplicate_suppressed")

        # 3. Check SMS audit log
        audit_res = self.client.get("/api/v1/alerts/sms/audit")
        self.assertEqual(audit_res.status_code, 200)
        audit_data = audit_res.json()
        self.assertGreaterEqual(audit_data["total"], 1)

    def test_websocket_heartbeat_and_handshake(self):
        """
        Tests WebSocket handshake and ping/pong keep-alive heartbeat.
        """
        test_mission = "WS-HEALTH-TEST"
        with self.client.websocket_connect(f"/ws/tracking/{test_mission}") as ws:
            handshake = ws.receive_json()
            self.assertEqual(handshake["type"], "connection_established")
            self.assertEqual(handshake["status"], "connected")

            # Heartbeat ping
            ws.send_text("ping")
            pong = ws.receive_text()
            self.assertEqual(pong, "pong")


if __name__ == "__main__":
    unittest.main()
