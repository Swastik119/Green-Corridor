"""
Phase 10 - Isolation Forest Unsupervised Anomaly Detection Engine.

Detects unusual ambulance journey behaviors including route deviations,
unapproved stoppages, telemetry gaps, and implausible kinematic changes.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest

from app.schemas.ai import AnomalyTelemetryInput, AnomalyDetectionResult

logger = logging.getLogger(__name__)


class JourneyAnomalyDetector:
    """
    Unsupervised journey anomaly detector utilizing Isolation Forest and heuristic validation.
    """

    def __init__(self) -> None:
        self.model: Optional[IsolationForest] = None
        self._initialize_baseline_model()

    def _initialize_baseline_model(self) -> None:
        """
        Fits an IsolationForest model on representative nominal convoy telemetry
        (speed 35-80 km/h, latency 1-5s, corridor centerline deviation 0-75m).
        """
        np.random.seed(42)
        n_samples = 800

        # Nominal operating distributions
        nominal_speeds = np.random.normal(55.0, 10.0, size=n_samples)
        nominal_speeds = np.clip(nominal_speeds, 25.0, 85.0)

        nominal_gaps = np.random.exponential(scale=2.5, size=n_samples)
        nominal_gaps = np.clip(nominal_gaps, 0.5, 8.0)

        nominal_deviations_m = np.random.exponential(scale=18.0, size=n_samples)
        nominal_deviations_m = np.clip(nominal_deviations_m, 0.0, 65.0)

        X_nominal = np.column_stack([nominal_speeds, nominal_gaps, nominal_deviations_m])

        iso = IsolationForest(
            n_estimators=100,
            contamination=0.04,
            random_state=42,
        )
        iso.fit(X_nominal)
        self.model = iso
        logger.info("Initialized baseline Isolation Forest anomaly detector (n_samples=%d)", n_samples)

    def evaluate_telemetry(self, input_data: AnomalyTelemetryInput) -> AnomalyDetectionResult:
        """
        Evaluates a live telemetry point for behavioral or route anomalies.
        """
        speed = input_data.speed
        gap_sec = input_data.last_update_gap_sec
        deviation_m = input_data.corridor_centerline_dist_m or 0.0

        features = np.array([[speed, gap_sec, deviation_m]])

        # Decision score: negative values indicate outliers/anomalies
        decision_score = float(self.model.decision_function(features)[0])
        model_is_anomaly = bool(self.model.predict(features)[0] == -1)

        # Rule-based contextual verification to avoid flagging minor GPS jitter
        anomaly_type = None
        severity = "NORMAL"
        action = "Convoy telemetry is nominal."
        is_anomaly = False

        if deviation_m > 350.0:
            is_anomaly = True
            anomaly_type = "ROUTE_DEVIATION"
            severity = "HIGH" if deviation_m < 800.0 else "CRITICAL"
            action = f"Verify ambulance current GPS route with driver. Vehicle is {deviation_m:.0f}m off designated green corridor."
        elif gap_sec > 60.0:
            is_anomaly = True
            anomaly_type = "GPS_SIGNAL_GAP"
            severity = "HIGH" if gap_sec < 180.0 else "CRITICAL"
            action = f"Telemetry dropped for {gap_sec:.0f} seconds. Attempt radio contact or SMS fallback."
        elif speed == 0.0 and gap_sec > 25.0:
            is_anomaly = True
            anomaly_type = "UNEXPECTED_STOP"
            severity = "HIGH"
            action = "Ambulance has stopped within active green corridor. Check traffic signal clearance at current junction."
        elif speed > 105.0:
            is_anomaly = True
            anomaly_type = "ERRATIC_SPEED"
            severity = "MEDIUM"
            action = f"Ambulance velocity ({speed:.0f} km/h) exceeds safe corridor profile limit (100 km/h)."
        elif model_is_anomaly and decision_score < -0.15:
            is_anomaly = True
            anomaly_type = "UNUSUAL_MOVEMENT"
            severity = "LOW"
            action = "Subtle telemetry drift detected. Monitor vehicle speed and heading."

        evidence = {
            "speed_kmh": round(speed, 1),
            "telemetry_gap_sec": round(gap_sec, 1),
            "corridor_deviation_m": round(deviation_m, 1),
            "isolation_forest_score": round(decision_score, 4),
        }

        return AnomalyDetectionResult(
            mission_id=input_data.mission_id,
            ambulance_id=input_data.ambulance_id,
            is_anomaly=is_anomaly,
            anomaly_score=round(decision_score, 4),
            anomaly_type=anomaly_type,
            severity=severity,
            supporting_evidence=evidence,
            recommended_action=action,
            evaluated_at=datetime.utcnow(),
        )


# Global singleton anomaly detector
anomaly_detector = JourneyAnomalyDetector()
