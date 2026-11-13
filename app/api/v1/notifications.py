from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["Notification Engine"])

class NotificationTriggerRequest(BaseModel):
    emergency_id: int
    route_data: dict
    police_stations: Optional[List[str]] = None

@router.post("/")
def trigger_notifications(data: NotificationTriggerRequest, db: Session = Depends(get_db)):
    """
    Triggers the notification and coordination engine for a given emergency and route.
    """
    try:
        alert_result = NotificationService.send_corridor_alerts(
            emergency_id=data.emergency_id,
            route_data=data.route_data,
            police_stations=data.police_stations
        )
        return {
            "status": "success",
            "message": "Corridor alerts dispatched successfully",
            "data": alert_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))