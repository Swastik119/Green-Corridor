from pydantic import BaseModel, Field, ConfigDict


class EmergencyRequestCreate(BaseModel):

    ambulance_id: int = Field(gt=0)

    destination_hospital_id: int = Field(gt=0)

    pickup_latitude: float = Field(ge=-90, le=90)

    pickup_longitude: float = Field(ge=-180, le=180)

    emergency_type: str = Field(min_length=2, max_length=50)

    priority: str = Field(
        pattern="^(low|medium|high|critical)$"
    )

    description: str | None = None


class EmergencyRequestResponse(BaseModel):

    id: int
    request_number: str
    ambulance_id: int
    requested_by: int
    destination_hospital_id: int
    emergency_type: str
    priority: str
    status: str

    model_config = ConfigDict(from_attributes=True)