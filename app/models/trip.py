from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography

from app.database.base import Base


class Trip(Base):

    __tablename__ = "trips"
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'active', 'completed', 'cancelled')",
            name="check_trip_status"
        ),
        Index("idx_trips_status", "status"),
Index("idx_trips_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    trip_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    emergency_request_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("emergency_requests.id"),
        unique=True,
        nullable=False
    )

    start_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

    end_location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

    route_geometry = mapped_column(
        Geography(geometry_type="LINESTRING", srid=4326),
        nullable=True
    )

    total_distance_meters: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    estimated_duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    actual_duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="planned",
        nullable=False
    )

    started_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
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
    emergency_request = relationship(
        "EmergencyRequest",
        back_populates="trip"
    )

    trip_stations = relationship(
        "TripStation",
        back_populates="trip"
    )
    location_updates = relationship(
        "LocationUpdate",
        back_populates="trip"
    )

    route_updates = relationship(
        "RouteUpdate",
        back_populates="trip"
    )