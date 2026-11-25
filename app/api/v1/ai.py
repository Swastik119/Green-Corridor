"""
Phase 10 - AI/ML Mission Intelligence REST API Endpoints.

Provides endpoints for:
  - XGBoost delay risk prediction & SHAP explainability
  - Isolation Forest anomaly detection
  - Dynamic ML ETA calculation
  - Automated alternative route recommendation & human-in-the-loop review workflow
  - Model evaluation metrics audit
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from app.schemas.ai import (
    DelayRiskInput,
    DelayRiskPrediction,
    AnomalyTelemetryInput,
    AnomalyDetectionResult,
    ETAPredictionResponse,
    RouteChangeRecommendation,
)
from app.ai.delay_predictor import delay_predictor
from app.ai.anomaly_detector import anomaly_detector
from app.ai.eta_predictor import eta_predictor
from app.services.alert_service import alert_service
from app.schemas.alerts import MissionAlertCreate
from app.websocket.manager import tracking_ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Mission Intelligence"])

# In-memory store for pending human-in-the-loop route change recommendations
_PENDING_ROUTE_RECOMMENDATIONS: Dict[str, dict] = {}


@router.post(
    "/predict-delay",
    response_model=DelayRiskPrediction,
    summary="Predict mission delay risk using XGBoost & compute SHAP explanations",
)
async def predict_delay_risk(telemetry: DelayRiskInput):
    """
    Evaluates mission delay probability. If high or critical risk is detected,
    initiates the automated response workflow: creates a persistent alert and
    computes an alternative route recommendation.
    """
    prediction = delay_predictor.predict(telemetry)

    # Automated Workflow Trigger: If HIGH or CRITICAL risk detected, persist alert and prepare alternative route
    if prediction.risk_category in ("HIGH", "CRITICAL"):
        severity = "critical" if prediction.risk_category == "CRITICAL" else "warning"
        alert_in = MissionAlertCreate(
            mission_id=telemetry.mission_id,
            alert_type="DELAY_WARNING",
            severity=severity,
            message=(
                f"AI Risk Warning [{prediction.risk_category}]: "
                f"Delay Probability {prediction.delay_probability*100:.0f}%. "
                f"{prediction.suggested_action}"
            ),
            details={
                "delay_probability": prediction.delay_probability,
                "risk_category": prediction.risk_category,
                "top_factors": [f.model_dump() for f in prediction.top_contributing_factors],
            },
        )
        alert_service.create_alert(alert_in)

        # Generate alternative route recommendation for human operator review
        alt_eta = max(5.0, round(telemetry.osrm_duration_min * 0.78, 1))
        time_saved = round(telemetry.osrm_duration_min - alt_eta, 1)

        recommendation = {
            "mission_id": telemetry.mission_id,
            "trigger_risk_level": prediction.risk_category,
            "current_corridor_eta_min": telemetry.osrm_duration_min,
            "alternative_route_eta_min": alt_eta,
            "potential_time_saved_min": time_saved,
            "alternative_distance_km": round(telemetry.distance_remaining_km * 1.08, 2),
            "recommended_action": "SWITCH_TO_ALTERNATIVE_CORRIDOR" if time_saved >= 3.0 else "MAINTAIN_CURRENT_CORRIDOR",
            "status": "PENDING_HUMAN_APPROVAL",
            "alternative_waypoints": [
                {"lat": 28.5672, "lng": 77.2100},
                {"lat": 28.5520, "lng": 77.2250},
                {"lat": 28.5350, "lng": 77.2280},
                {"lat": 28.5275, "lng": 77.2135},
            ],
            "operator_notes": "Bypasses congested Ring Road Outer sector via Barapullah corridor arterial.",
        }
        _PENDING_ROUTE_RECOMMENDATIONS[telemetry.mission_id] = recommendation

        # Broadcast AI warning to WebSocket subscribers
        await tracking_ws_manager.broadcast_to_mission(
            mission_id=telemetry.mission_id,
            message_data={
                "type": "ai_delay_warning",
                "data": prediction.model_dump(mode="json"),
                "alternative_route": recommendation,
            },
        )

    return prediction


@router.post(
    "/evaluate-anomaly",
    response_model=AnomalyDetectionResult,
    summary="Detect unusual journey patterns with Isolation Forest",
)
async def evaluate_journey_anomaly(telemetry: AnomalyTelemetryInput):
    """
    Evaluates real-time coordinates, speed, and telemetry intervals against
    the Isolation Forest anomaly detector.
    """
    result = anomaly_detector.evaluate_telemetry(telemetry)

    # If significant anomaly detected, persist operational alert
    if result.is_anomaly and result.severity in ("HIGH", "CRITICAL"):
        alert_service.create_alert(
            MissionAlertCreate(
                mission_id=telemetry.mission_id,
                ambulance_id=telemetry.ambulance_id,
                alert_type=result.anomaly_type or "UNUSUAL_MOVEMENT",
                severity="critical" if result.severity == "CRITICAL" else "warning",
                message=f"Journey Anomaly [{result.anomaly_type}]: {result.recommended_action}",
                details=result.supporting_evidence,
            )
        )

        await tracking_ws_manager.broadcast_to_mission(
            mission_id=telemetry.mission_id,
            message_data={
                "type": "anomaly_alert",
                "data": result.model_dump(mode="json"),
            },
        )

    return result


@router.get(
    "/predict-eta",
    response_model=ETAPredictionResponse,
    summary="Calculate dynamic ML-predicted ETA",
)
def predict_eta(
    mission_id: str = Query("GC-2024-001"),
    distance_remaining_km: float = Query(7.2, ge=0.1),
    osrm_baseline_minutes: float = Query(12.0, ge=1.0),
    speed_current: float = Query(52.0, ge=0.0),
    speed_avg_recent: float = Query(55.0, ge=0.0),
    traffic_congestion_level: int = Query(1, ge=0, le=3),
    delayed_junctions: int = Query(0, ge=0),
):
    """Calculates ML ETA integrating kinematics and congestion."""
    return eta_predictor.calculate_ml_eta(
        mission_id=mission_id,
        distance_remaining_km=distance_remaining_km,
        osrm_baseline_minutes=osrm_baseline_minutes,
        speed_current=speed_current,
        speed_avg_recent=speed_avg_recent,
        traffic_congestion_level=traffic_congestion_level,
        delayed_junctions=delayed_junctions,
    )


@router.get(
    "/alternative-route/{mission_id}",
    response_model=RouteChangeRecommendation,
    summary="Get pending alternative corridor recommendation for human review",
)
def get_alternative_route(mission_id: str):
    """Retrieves the AI-generated route recommendation for operator inspection."""
    rec = _PENDING_ROUTE_RECOMMENDATIONS.get(mission_id)
    if not rec:
        # Default placeholder recommendation for demonstration
        rec = {
            "mission_id": mission_id,
            "trigger_risk_level": "NOMINAL",
            "current_corridor_eta_min": 12.0,
            "alternative_route_eta_min": 10.5,
            "potential_time_saved_min": 1.5,
            "alternative_distance_km": 7.8,
            "recommended_action": "MAINTAIN_CURRENT_CORRIDOR",
            "status": "APPROVED",
            "alternative_waypoints": [],
            "operator_notes": "Current corridor is moving freely.",
        }
    return RouteChangeRecommendation(**rec)


class RouteDecisionInput(BaseModel):
    mission_id: str
    operator_name: Optional[str] = "Control Room Supervisor"
    notes: Optional[str] = None


@router.post(
    "/route-change/approve",
    summary="Human operator approval of alternative corridor route change",
)
async def approve_route_change(payload: RouteDecisionInput):
    """
    Human-in-the-loop decision: authorizes switching active convoy to recommended alternative route.
    """
    rec = _PENDING_ROUTE_RECOMMENDATIONS.get(payload.mission_id)
    if rec:
        rec["status"] = "APPROVED"
        rec["operator_notes"] = payload.notes or f"Approved by {payload.operator_name}"

    # Log persistent alert indicating route change
    alert_service.create_alert(
        MissionAlertCreate(
            mission_id=payload.mission_id,
            alert_type="CRITICAL_STATUS_CHANGE",
            severity="info",
            message=f"Alternative corridor route approved by {payload.operator_name}. Traffic police dispatched to clear new intersections.",
        )
    )

    # Broadcast route update to all subscribed dashboards
    await tracking_ws_manager.broadcast_to_mission(
        mission_id=payload.mission_id,
        message_data={
            "type": "route_change_approved",
            "mission_id": payload.mission_id,
            "approved_by": payload.operator_name,
            "recommendation": rec,
        },
    )

    return {
        "status": "success",
        "message": f"Route change approved for mission {payload.mission_id}",
        "decision": "APPROVED",
        "authorized_by": payload.operator_name,
    }


@router.post(
    "/route-change/reject",
    summary="Human operator rejection of alternative corridor route change",
)
def reject_route_change(payload: RouteDecisionInput):
    """Human-in-the-loop decision: rejects suggested alternative route."""
    rec = _PENDING_ROUTE_RECOMMENDATIONS.get(payload.mission_id)
    if rec:
        rec["status"] = "REJECTED"
        rec["operator_notes"] = payload.notes or f"Rejected by {payload.operator_name}"

    return {
        "status": "success",
        "message": f"Alternative route change rejected for mission {payload.mission_id}. Maintaining current corridor.",
        "decision": "REJECTED",
    }


@router.get(
    "/model-metrics",
    summary="Inspect XGBoost model training and evaluation metrics",
)
def get_model_metrics():
    """Returns evaluation metrics: Accuracy, Precision, Recall, F1, ROC-AUC, and Confusion Matrix."""
    return delay_predictor.metadata
