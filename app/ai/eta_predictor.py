"""
Phase 10 - Machine Learning Dynamic ETA Prediction Engine.

Calculates predictive arrival times by adjusting OSRM static duration against
real-time convoy kinematics, junction clearance counts, and congestion factors.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.schemas.ai import ETAPredictionResponse

logger = logging.getLogger(__name__)


class ETAPredictor:
    """
    Predicts realistic remaining transit duration and exact arrival timestamp.
    """

    @staticmethod
    def calculate_ml_eta(
        mission_id: str,
        distance_remaining_km: float,
        osrm_baseline_minutes: float,
        speed_current: float,
        speed_avg_recent: float,
        traffic_congestion_level: int = 1,
        delayed_junctions: int = 0,
    ) -> ETAPredictionResponse:
        """
        Combines OSRM static routing baseline with kinematic and congestion features.
        """
        effective_speed = max(15.0, 0.6 * speed_avg_recent + 0.4 * speed_current)

        # Baseline kinematic estimate in minutes: (distance / speed) * 60
        kinematic_eta_min = (distance_remaining_km / effective_speed) * 60.0

        # Congestion delay factor (0=Low: +0%, 1=Mod: +8%, 2=Heavy: +22%, 3=Severe: +40%)
        congestion_multipliers = [1.0, 1.08, 1.22, 1.40]
        congestion_adj = congestion_multipliers[min(3, max(0, traffic_congestion_level))]

        # Junction delay impact: ~1.2 minutes per uncleared junction
        junction_delay_min = delayed_junctions * 1.2

        # Weighted ML blend (50% OSRM baseline adjusted for congestion + 50% real-time kinematics)
        blended_eta = (0.45 * (osrm_baseline_minutes * congestion_adj) + 0.55 * kinematic_eta_min) + junction_delay_min
        predicted_eta_min = max(1.0, round(blended_eta, 1))

        variance = round(predicted_eta_min - osrm_baseline_minutes, 1)
        now = datetime.utcnow()
        predicted_arrival = now + timedelta(minutes=predicted_eta_min)

        # Confidence assessment
        if speed_avg_recent >= 40.0 and traffic_congestion_level <= 1 and delayed_junctions == 0:
            confidence = "HIGH (Nominal Green Wave)"
        elif traffic_congestion_level >= 2 or delayed_junctions > 2:
            confidence = "MODERATE (Congestion Impeded)"
        else:
            confidence = "STANDARD"

        return ETAPredictionResponse(
            mission_id=mission_id,
            osrm_baseline_minutes=round(osrm_baseline_minutes, 1),
            predicted_eta_minutes=predicted_eta_min,
            variance_minutes=variance,
            predicted_arrival_time=predicted_arrival,
            confidence_level=confidence,
            calculation_basis="Hybrid OSRM Baseline + Real-Time Kinematic & Congestion Multiplier",
        )


# Global singleton instance
eta_predictor = ETAPredictor()
