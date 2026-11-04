from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column , relationship

from app.database.base import Base


class Ambulance(Base):

    __tablename__ = "ambulances"
    __table_args__ = (
        CheckConstraint(
            "status IN ('available', 'on_trip', 'maintenance', 'offline')",
            name="check_ambulance_status"
        ),
        Index(
            "idx_ambulances_current_operator_id",
            "current_operator_id"
        ),
        Index(
            "idx_ambulances_status",
            "status"
        ),
    )
    

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    registration_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    vehicle_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    ambulance_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    current_operator_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="available",
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
    current_operator = relationship(
        "User",
        back_populates="operated_ambulances"
    )
    emergency_requests = relationship(
        "EmergencyRequest",
        back_populates="ambulance"
    )