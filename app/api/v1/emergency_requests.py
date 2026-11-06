from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.emergency_request import (
    EmergencyRequestCreate,
    EmergencyRequestResponse
)
from app.services.emergency_request_service import create_emergency_request
from app.deps import require_role
from app.models.user import User

router = APIRouter(
    prefix="/emergency-requests",
    tags=["Emergency Requests"]
)


@router.post(
    "/",
    response_model=EmergencyRequestResponse,
    status_code=status.HTTP_201_CREATED
)
def create_request(
    request: EmergencyRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ambulance_operator"))
):
    try:
        new_request = create_emergency_request(
            db=db,
            ambulance_id=request.ambulance_id,
            requested_by=current_user.id,
            destination_hospital_id=request.destination_hospital_id,
            pickup_latitude=request.pickup_latitude,
            pickup_longitude=request.pickup_longitude,
            emergency_type=request.emergency_type,
            priority=request.priority,
            description=request.description
        )

        return new_request

    except ValueError as error:
        error_message = str(error)

        if error_message == "Ambulance is not available":
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_404_NOT_FOUND

        raise HTTPException(
            status_code=status_code,
            detail=error_message
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )