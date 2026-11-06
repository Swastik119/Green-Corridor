
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select
from geoalchemy2.elements import WKTElement

from app.models.user import User
from app.models.emergency_request import EmergencyRequest
from app.models.ambulance import Ambulance
from app.models.hospital import Hospital


def create_emergency_request(
    db: Session,
    ambulance_id: int,
    requested_by: int,
    destination_hospital_id: int,
    pickup_latitude: float,
    pickup_longitude: float,
    emergency_type: str,
    priority: str,
    description: str | None = None
):
    # 1. Check whether requester exists
    requester = db.get(User, requested_by)

    if requester is None:
        raise ValueError("Requester not found")

    # 2. Check whether ambulance exists and lock its row
    ambulance = db.execute(
        select(Ambulance)
        .where(Ambulance.id == ambulance_id)
        .with_for_update()
    ).scalar_one_or_none()

    if ambulance is None:
        raise ValueError("Ambulance not found")

    # 3. Check whether ambulance is available
    if ambulance.status != "available":
        raise ValueError("Ambulance is not available")

    # 4. Check whether destination hospital exists
    hospital = db.get(Hospital, destination_hospital_id)

    if hospital is None:
        raise ValueError("Destination hospital not found")

    # 5. Generate unique request number
    request_number = f"GC-REQ-{uuid.uuid4().hex[:8].upper()}"

    # 6. Convert coordinates into PostGIS POINT
    pickup_location = WKTElement(
        f"POINT({pickup_longitude} {pickup_latitude})",
        srid=4326
    )

    # 7. Create emergency request
    emergency_request = EmergencyRequest(
        request_number=request_number,
        ambulance_id=ambulance_id,
        requested_by=requested_by,
        destination_hospital_id=destination_hospital_id,
        pickup_location=pickup_location,
        emergency_type=emergency_type,
        priority=priority,
        description=description,
        status="pending"
    )

    # 8. Save request and update ambulance atomically
    try:
        db.add(emergency_request)

        ambulance.status = "on_trip"

        db.commit()

    except Exception:
        db.rollback()
        raise

    # 9. Refresh and return the saved request
    db.refresh(emergency_request)

    return emergency_request
