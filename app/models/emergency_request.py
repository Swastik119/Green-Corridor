from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column , relationship
from geoalchemy2 import Geography

from app.database.base import Base


class EmergencyRequest(Base):

    __tablename__ = "emergency_requests"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="check_emergency_priority"
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'active', 'completed', 'cancelled')",
            name="check_emergency_status"
        ),
        Index(
            "idx_emergency_requests_ambulance_id",
            "ambulance_id"
        ),
        Index(
            "idx_emergency_requests_requested_by",
            "requested_by"
        ),
        Index(
            "idx_emergency_requests_destination_hospital_id",
            "destination_hospital_id"
        ),
        Index(
            "idx_emergency_requests_status",
            "status"
        ),
        Index(
            "idx_emergency_requests_priority",
            "priority"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    request_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    ambulance_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("ambulances.id"),
        nullable=False
    )

    requested_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    destination_hospital_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("hospitals.id"),
        nullable=False
    )

    pickup_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

    emergency_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    ambulance = relationship(
        "Ambulance",
        back_populates="emergency_requests"
    )

    requester = relationship(
        "User",
        back_populates="emergency_requests"
    )

    destination_hospital = relationship(
        "Hospital",
        back_populates="emergency_requests"
    )
    trip = relationship(
        "Trip",
        back_populates="emergency_request",
        uselist=False
    )