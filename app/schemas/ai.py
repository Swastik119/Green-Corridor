"""
Phase 10 - AI/ML Mission Intelligence Schemas.

Validates telemetry inputs, prediction outputs, SHAP explainability payloads,
anomaly detection results, and human-in-the-loop route change reviews.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class DelayRiskInput(BaseModel):
    """
    Structured feature vector input for the XGBoost delay risk prediction engine.
    """
    mission_id: str = Field(..., description="Unique mission identifier (e.g. GC-2024-001)")
    speed_current: float = Field(..., ge=0.0, le=200.0, description="Current ambulance speed in km/h")
    speed_avg_recent: float = Field(..., ge=0.0, le=200.0, description="Average speed over last 5 minutes in km/h")
    distance_remaining_km: float = Field(..., ge=0.0, le=500.0, description="Remaining distance to destination in km")
    osrm_duration_min: float = Field(..., ge=0.0, le=600.0, description="OSRM baseline route duration in minutes")
    elapsed_time_min: float = Field(..., ge=0.0, le=600.0, description="Minutes elapsed since mission departure")
    traffic_congestion_level: int = Field(1, ge=0, le=3, description="0=Low, 1=Moderate, 2=Heavy, 3=Severe")
    delayed_junctions_count: int = Field(0, ge=0, le=50, description="Number of junctions where green wave clearance was delayed")
    route_deviation_flag: int = Field(0, ge=0, le=1, description="1 if ambulance has deviated from assigned corridor, 0 otherwise")
    gps_gap_seconds: float = Field(0.0, ge=0.0, le=3600.0, description="Time gap between consecutive GPS updates in seconds")
    hour_of_day: Optional[int] = Field(None, ge=0, le=23, description="Hour of the day (0-23)")
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of the week (0=Mon, 6=Sun)")


class FeatureContribution(BaseModel):
    """
    SHAP-derived feature contribution towards delay prediction.
    """
    feature: str
    feature_value: float
    shap_value: float
    impact: Literal["increases_delay_risk", "decreases_delay_risk"]
    description: str


class DelayRiskPrediction(BaseModel):
    """
    Output of the XGBoost Mission Delay Risk Prediction Engine.
    """
    mission_id: str
    delay_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of significant transit delay [0.0, 1.0]")
    risk_category: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    predicted_delay: bool
    prediction_timestamp: datetime
    model_version: str = "xgboost-delay-v1.0.0"
    top_contributing_factors: List[FeatureContribution] = Field(default_factory=list)
    suggested_action: str


class AnomalyTelemetryInput(BaseModel):
    """
    Telemetry frame evaluated by the Isolation Forest Unsupervised Anomaly Detector.
    """
    mission_id: str
    ambulance_id: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed: float = Field(..., ge=0.0, le=250.0)
    last_update_gap_sec: float = Field(0.0, ge=0.0)
    corridor_centerline_dist_m: Optional[float] = Field(0.0, ge=0.0, description="Distance in meters from designated corridor centerline")


class AnomalyDetectionResult(BaseModel):
    """
    Output from the Isolation Forest Anomaly Detection component.
    """
    mission_id: str
    ambulance_id: str
    is_anomaly: bool
    anomaly_score: float = Field(..., description="Raw decision score from Isolation Forest (negative indicates anomaly)")
    anomaly_type: Optional[str] = Field(None, description="ROUTE_DEVIATION, UNEXPECTED_STOP, GPS_SIGNAL_GAP, ERRATIC_SPEED")
    severity: Literal["NORMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    supporting_evidence: Dict[str, Any] = Field(default_factory=dict)
    recommended_action: str
    evaluated_at: datetime


class ETAPredictionResponse(BaseModel):
    """
    Machine Learning dynamic ETA calculation comparing baseline OSRM with ML-predicted arrival.
    """
    mission_id: str
    osrm_baseline_minutes: float
    predicted_eta_minutes: float
    variance_minutes: float
    predicted_arrival_time: datetime
    confidence_level: str
    calculation_basis: str


class RouteChangeRecommendation(BaseModel):
    """
    Automated alternative route workflow initiated upon detection of High/Critical delay risk.
    """
    mission_id: str
    trigger_risk_level: str
    current_corridor_eta_min: float
    alternative_route_eta_min: float
    potential_time_saved_min: float
    alternative_distance_km: float
    recommended_action: Literal["SWITCH_TO_ALTERNATIVE_CORRIDOR", "MAINTAIN_CURRENT_CORRIDOR"]
    status: Literal["PENDING_HUMAN_APPROVAL", "APPROVED", "REJECTED"]
    alternative_waypoints: List[Dict[str, float]] = Field(default_factory=list)
    operator_notes: Optional[str] = None
