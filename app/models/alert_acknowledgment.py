from sqlalchemy import (
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AlertAcknowledgment(Base):

    __tablename__ = "alert_acknowledgments"
    __table_args__ = (
        CheckConstraint(
            "acknowledgment_status IN ('acknowledged', 'action_started', 'unable_to_respond')",
            name="check_acknowledgment_status"
        ),
        Index(
        "idx_alert_acknowledgments_station_alert_id",
        "station_alert_id"
    ),
    Index(
        "idx_alert_acknowledgments_acknowledged_by",
        "acknowledged_by"
    ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    station_alert_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("station_alerts.id"),
        nullable=False
    )

    acknowledged_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    acknowledgment_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    acknowledged_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    acknowledged_user = relationship(
        "User",
        back_populates="alert_acknowledgments"
    )
    station_alert = relationship(
        "StationAlert",
        back_populates="acknowledgments"
    )