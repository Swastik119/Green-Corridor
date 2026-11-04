from sqlalchemy import (
    BigInteger,
    Float,
    DateTime,
    ForeignKey,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography

from app.database.base import Base


class LocationUpdate(Base):

    __tablename__ = "location_updates"
    __table_args__ = (
        Index(
            "idx_location_updates_trip_id",
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

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

    speed_kmh: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    recorded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    trip = relationship(
        "Trip",
        back_populates="location_updates"
    )