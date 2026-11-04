from sqlalchemy import (
    BigInteger,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TripStation(Base):

    __tablename__ = "trip_stations"

    __table_args__ = (
        UniqueConstraint(
            "trip_id",
            "police_station_id",
            name="uq_trip_station"
        ),
        UniqueConstraint(
            "trip_id",
            "sequence_number",
            name="uq_trip_station_sequence"
        ),
        Index(
            "idx_trip_stations_police_station_id",
            "police_station_id"
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

    police_station_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("police_stations.id"),
        nullable=False
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    distance_from_start_meters: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    estimated_arrival_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    station_alerts = relationship(
        "StationAlert",
        back_populates="trip_station"
    )
    police_station = relationship(
        "PoliceStation",
        back_populates="trip_stations"
    )
    trip = relationship(
        "Trip",
        back_populates="trip_stations"
    )