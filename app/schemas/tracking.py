"""
Phase 8 - Real-Time Tracking Pydantic Schemas.
Validates GPS updates, connection telemetry, and simulator controls.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class GPSUpdate(BaseModel):
    """
    Standard GPS update payload transmitted by ambulances or the GPS simulator.
    """
    mission_id: str = Field(..., description="Unique identifier for the mission (e.g. GC-2024-001)")
    ambulance_id: str = Field(..., description="Ambulance identifier (e.g. AMB-001)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 Latitude between -90.0 and 90.0")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 Longitude between -180.0 and 180.0")
    speed: float = Field(..., ge=0.0, le=250.0, description="Vehicle speed in km/h (0.0 to 250.0)")
    heading: Optional[float] = Field(None, ge=0.0, le=360.0, description="Compass heading in degrees (0.0 to 360.0)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="UTC timestamp of the GPS reading")
    is_simulated: bool = Field(False, description="Flag indicating whether this is simulated telemetry")
    eta_minutes: Optional[int] = Field(None, ge=0, description="Updated estimated minutes to destination")
    distance_remaining_km: Optional[float] = Field(None, ge=0.0, description="Estimated remaining distance in km")

    @field_validator("mission_id", "ambulance_id")
    @classmethod
    def not_empty(cls, v: str) -> str:
        s = str(v).strip()
        if not s:
            raise ValueError("Field cannot be empty")
        return s


class GPSUpdateResponse(BaseModel):
    """
    Response acknowledging receipt and broadcast of a GPS update.
    """
    status: str = "success"
    message: str
    broadcast_clients: int = Field(0, description="Number of active WebSocket clients that received this update")
    data: GPSUpdate


class SimulatorConfig(BaseModel):
    """
    Configuration parameters for starting the GPS movement simulator.
    """
    mission_id: str = Field("GC-2024-001", description="Mission ID to simulate")
    ambulance_id: str = Field("AMB-001", description="Ambulance ID to simulate")
    interval_seconds: float = Field(2.0, ge=0.5, le=10.0, description="Interval between simulated GPS ticks in seconds")
    speed_kmh: float = Field(55.0, ge=10.0, le=120.0, description="Simulated cruising speed in km/h")
    loop: bool = Field(True, description="Whether to loop the route once destination is reached")


class SimulatorStatus(BaseModel):
    """
    Status of the simulated GPS movement engine.
    """
    is_running: bool
    active_missions: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class OfflineGPSItem(BaseModel):
    """
    Single offline queued GPS telemetry record.
    """
    idempotency_key: str = Field(..., description="Unique client-generated idempotency key")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed: float = Field(..., ge=0.0, le=250.0)
    heading: Optional[float] = Field(None, ge=0.0, le=360.0)
    timestamp: datetime = Field(..., description="Original timestamp when recorded offline")
    is_simulated: bool = Field(False)


class SyncBatchRequest(BaseModel):
    """
    Batch payload sent by client upon network reconnection to synchronize pending GPS data.
    """
    mission_id: str = Field(..., description="Target mission identifier")
    ambulance_id: str = Field(..., description="Target ambulance identifier")
    updates: list[OfflineGPSItem] = Field(..., min_length=1, max_length=500, description="Chronological offline telemetry items")


class SyncBatchResponse(BaseModel):
    """
    Result of batch synchronization.
    """
    status: str = "success"
    mission_id: str
    received_count: int
    synced_count: int
    duplicates_skipped: int
    latest_synchronized_at: Optional[datetime] = None
