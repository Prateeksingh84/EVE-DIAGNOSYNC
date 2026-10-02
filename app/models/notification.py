import enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    func,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationChannel(str, enum.Enum):
    """Notification delivery channel."""
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"


class NotificationStatus(str, enum.Enum):
    """Notification dispatch status."""
    SENT = "SENT"
    PENDING = "PENDING"
    FAILED = "FAILED"


class Notification(Base):
    """Audit log of user notifications (simulated email, SMS, and in-app alerts)."""

    __tablename__ = "notifications"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    booking_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel = Column(
        SQLEnum(NotificationChannel),
        default=NotificationChannel.EMAIL,
        nullable=False,
    )
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(
        SQLEnum(NotificationStatus),
        default=NotificationStatus.SENT,
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", backref="notifications")
    booking = relationship("Booking", backref="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, subject={self.subject})>"
