from sqlalchemy import (
    BigInteger,
    Integer,
    Float,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography

from app.database.base import Base


class RouteUpdate(Base):

    __tablename__ = "route_updates"

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "version_number"
        ),
        Index(
        "idx_route_updates_trip_id",
        "trip_id"
    ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    trip_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("trips.id"),
        nullable=False
    )

    route_geometry = mapped_column(
        Geography(geometry_type="LINESTRING", srid=4326),
        nullable=False
    )

    distance_meters: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    estimated_duration_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    change_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    trip = relationship(
        "Trip",
        back_populates="route_updates"
    )