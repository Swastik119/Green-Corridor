import enum
from sqlalchemy import (
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    CheckConstraint,
    Index,
    func
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AMBULANCE_OPERATOR = "ambulance_operator"
    POLICE_OFFICER = "police_officer"
    HOSPITAL_STAFF = "hospital_staff"


class User(Base):

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'ambulance_operator', 'police_officer', 'hospital_staff')",
            name="check_user_role"
        ),
        Index("idx_users_role", "role"),
        Index("idx_users_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    phone: Mapped[str | None] = mapped_column(
        String(15),
        unique=True,
        nullable=True
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(30),
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

    operated_ambulances = relationship(
        "Ambulance",
        back_populates="current_operator"
    )

    emergency_requests = relationship(
        "EmergencyRequest",
        back_populates="requester"
    )

    alert_acknowledgments = relationship(
        "AlertAcknowledgment",
        back_populates="acknowledged_user"
    )