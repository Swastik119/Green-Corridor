from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class StationAlert(Base):

    __tablename__ = "station_alerts"
    __table_args__ = (
        CheckConstraint(
            "delivery_status IN ('pending', 'sent', 'failed')",
            name="check_alert_delivery_status"
        ),
        Index(
            "idx_station_alerts_trip_station_id",
            "trip_station_id"
        ),
        Index(
            "idx_station_alerts_delivery_status",
            "delivery_status"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    trip_station_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("trip_stations.id"),
        nullable=False
    )

    alert_message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    ambulance_latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    ambulance_longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    ambulance_speed: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    eta_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    delivery_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False
    )

    sent_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    acknowledgments = relationship(
        "AlertAcknowledgment",
        back_populates="station_alert"
    )
    trip_station = relationship(
        "TripStation",
        back_populates="station_alerts"
    )