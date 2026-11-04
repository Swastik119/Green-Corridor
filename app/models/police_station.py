from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography

from app.database.base import Base


class PoliceStation(Base):

    __tablename__ = "police_stations"
    __table_args__ = (
    Index("idx_police_stations_city", "city"),
    Index("idx_police_stations_is_active", "is_active"),
)

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    phone: Mapped[str] = mapped_column(
        String(15),
        nullable=False
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False
    )

    jurisdiction_radius: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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
    trip_stations = relationship(
        "TripStation",
        back_populates="police_station"
    )