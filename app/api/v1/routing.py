from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.routing_service import get_route_from_osrm

router = APIRouter(prefix="/api/v1/routing", tags=["Routing Engine"])

class RouteRequest(BaseModel):
    start_latitude: float
    start_longitude: float
    end_latitude: float
    end_longitude: float


@router.post("/")
def calculate_ambulance_route(data: RouteRequest, db: Session = Depends(get_db)):
    route_data = get_route_from_osrm(
        start_lon=data.start_longitude,
        start_lat=data.start_latitude,
        end_lon=data.end_longitude,
        end_lat=data.end_latitude
    )
    return {
        "status": "success",
        "routing_engine": "osrm",
        "route": route_data
    }