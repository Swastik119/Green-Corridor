"""
Phase 8 - Real-Time Tracking REST API Endpoints.

Handles GPS telemetry ingestion, historical coordinates retrieval,
and GPS movement simulation controls.
"""

from __future__ import annotations

import logging
from typing import List, Optional
from datetime import datetime
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.schemas.tracking import (
    GPSUpdate,
    GPSUpdateResponse,
    SimulatorConfig,
    SimulatorStatus,
    SyncBatchRequest,
    SyncBatchResponse,
)
from app.websocket.manager import tracking_ws_manager
from app.services.gps_simulator import gps_simulator
from app.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tracking", tags=["Real-Time Tracking"])

# In-memory recent GPS history ring buffer: mission_id -> deque of recent updates (max 100)
_GPS_HISTORY: dict[str, deque[dict]] = defaultdict(lambda: deque(maxlen=100))

# Idempotency tracking to prevent duplicate ingestion of offline updates
_SEEN_IDEMPOTENCY_KEYS: set[str] = set()


@router.post(
    "/gps",
    response_model=GPSUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit and broadcast live ambulance GPS coordinates",
)
async def submit_gps_update(
    update: GPSUpdate,
    db: Session = Depends(get_db),
):
    """
    Ingests a validated GPS telemetry packet from an ambulance unit or simulator,
    records it to the location history, and broadcasts it across WebSockets to all
    subscribers of that mission.
    """
    # 1. Record update in in-memory history ring buffer
    payload_dict = update.model_dump(mode="json")
    _GPS_HISTORY[update.mission_id].append(payload_dict)

    # 2. Persist to database if trip exists (PostgreSQL + PostGIS or SQLite)
    try:
        from app.models.trip import Trip
        from app.models.location_update import LocationUpdate
        from geoalchemy2.elements import WKTElement

        # Look up trip by trip_number or numeric id if matches
        trip = None
        if update.mission_id.isdigit():
            trip = db.get(Trip, int(update.mission_id))
        if not trip:
            trip = db.query(Trip).filter(Trip.trip_number == update.mission_id).first()

        if trip:
            loc_point = WKTElement(
                f"POINT({update.longitude} {update.latitude})",
                srid=4326,
            )
            loc_rec = LocationUpdate(
                trip_id=trip.id,
                location=loc_point,
                speed_kmh=update.speed,
                recorded_at=update.timestamp or datetime.utcnow(),
            )
            db.add(loc_rec)
            db.commit()
    except Exception as db_err:
        # Graceful fallback: do not fail live telemetry if DB is offline or mock mission
        logger.debug("Database location persistence skipped: %s", db_err)
        db.rollback()

    # 3. Broadcast to all active WebSocket clients subscribed to this mission
    recipients_count = await tracking_ws_manager.broadcast_to_mission(
        mission_id=update.mission_id,
        message_data={
            "type": "gps_update",
            "data": payload_dict,
        },
    )

    return GPSUpdateResponse(
        status="success",
        message="GPS update processed and broadcast successfully",
        broadcast_clients=recipients_count,
        data=update,
    )


@router.get(
    "/history/{mission_id}",
    summary="Retrieve recent GPS trail for a mission",
)
def get_gps_history(mission_id: str):
    """
    Returns the recent coordinates trail recorded for the given mission.
    """
    history = list(_GPS_HISTORY.get(mission_id, []))
    return {
        "status": "success",
        "mission_id": mission_id,
        "total_points": len(history),
        "history": history,
    }


@router.post(
    "/simulator/start",
    summary="Start simulated ambulance GPS movement",
)
async def start_simulator(config: Optional[SimulatorConfig] = None):
    """
    Initiates simulated GPS movement along the pre-configured emergency corridor.
    """
    cfg = config or SimulatorConfig()
    success = await gps_simulator.start(cfg)
    if not success:
        return {
            "status": "warning",
            "message": f"Simulator already active for mission {cfg.mission_id}",
            "mission_id": cfg.mission_id,
        }

    return {
        "status": "success",
        "message": f"GPS simulator started for mission {cfg.mission_id} ({cfg.ambulance_id})",
        "config": cfg.model_dump(),
    }


@router.post(
    "/simulator/stop",
    summary="Stop simulated ambulance GPS movement",
)
async def stop_simulator(mission_id: Optional[str] = Query(None)):
    """
    Stops active GPS simulations.
    """
    stopped = await gps_simulator.stop(mission_id)
    return {
        "status": "success",
        "message": (
            f"Simulator stopped for mission {mission_id}"
            if mission_id
            else "All running simulators stopped"
        ),
        "stopped": stopped,
    }


@router.get(
    "/simulator/status",
    summary="Get GPS movement simulator status",
)
def get_simulator_status():
    """
    Returns current simulator execution state and active simulated missions.
    """
    return gps_simulator.get_status()


@router.get(
    "/subscribers",
    summary="Get active WebSocket tracking subscribers",
)
def get_subscribers(mission_id: Optional[str] = Query(None)):
    """
    Returns number of active WebSocket connections.
    """
    return {
        "status": "success",
        "mission_id": mission_id,
        "active_subscribers": tracking_ws_manager.get_active_count(mission_id),
        "active_missions": tracking_ws_manager.get_active_missions(),
    }


@router.post(
    "/sync",
    response_model=SyncBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch synchronize offline queued GPS updates upon reconnection",
)
async def sync_offline_gps(
    batch: SyncBatchRequest,
):
    """
    Ingests and validates queued offline GPS telemetry records once network is restored.
    Applies idempotency filtering to prevent duplicates and updates telemetry history chronologically.
    """
    global _SEEN_IDEMPOTENCY_KEYS

    received = len(batch.updates)
    synced = 0
    skipped = 0
    latest_ts = None
    latest_item = None

    # Sort updates chronologically by timestamp
    sorted_updates = sorted(batch.updates, key=lambda x: x.timestamp)

    for item in sorted_updates:
        # Deduplication check
        if item.idempotency_key in _SEEN_IDEMPOTENCY_KEYS:
            skipped += 1
            continue

        _SEEN_IDEMPOTENCY_KEYS.add(item.idempotency_key)
        # Prevent unbounded set growth
        if len(_SEEN_IDEMPOTENCY_KEYS) > 10000:
            _SEEN_IDEMPOTENCY_KEYS.clear()

        # Build telemetry record
        record = {
            "mission_id": batch.mission_id,
            "ambulance_id": batch.ambulance_id,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "speed": item.speed,
            "heading": item.heading,
            "timestamp": item.timestamp.isoformat(),
            "is_simulated": item.is_simulated,
            "is_offline_sync": True,
        }

        _GPS_HISTORY[batch.mission_id].append(record)
        synced += 1

        if latest_ts is None or item.timestamp > latest_ts:
            latest_ts = item.timestamp
            latest_item = record

    # Broadcast synchronization notification over WebSocket
    if synced > 0 and latest_item:
        await tracking_ws_manager.broadcast_to_mission(
            mission_id=batch.mission_id,
            message_data={
                "type": "gps_sync_completed",
                "mission_id": batch.mission_id,
                "synced_count": synced,
                "duplicates_skipped": skipped,
                "data": latest_item,
            },
        )

    logger.info(
        "Batch synced %d offline GPS updates for mission [%s] (%d duplicates skipped)",
        synced,
        batch.mission_id,
        skipped,
    )

    return SyncBatchResponse(
        status="success",
        mission_id=batch.mission_id,
        received_count=received,
        synced_count=synced,
        duplicates_skipped=skipped,
        latest_synchronized_at=latest_ts,
    )
