import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base


class DiagnosticCentre(Base):
    """Model representing a diagnostic centre/lab."""

    __tablename__ = "diagnostic_centres"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    centre_tests = relationship(
        "CentreTest", back_populates="centre", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DiagnosticCentre(id={self.id}, name={self.name})>"


class DiagnosticTest(Base):
    """Model representing a type of diagnostic test."""

    __tablename__ = "diagnostic_tests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    centre_tests = relationship(
        "CentreTest", back_populates="test", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DiagnosticTest(id={self.id}, name={self.name})>"


class CentreTest(Base):
    """Junction model linking diagnostic centres to their available tests with pricing."""

    __tablename__ = "centre_tests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    centre_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("diagnostic_centres.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("diagnostic_tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    price = Column(Numeric(10, 2), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("centre_id", "test_id", name="uq_centre_test"),
    )

    # Relationships
    centre = relationship("DiagnosticCentre", back_populates="centre_tests")
    test = relationship("DiagnosticTest", back_populates="centre_tests")
    bookings = relationship("Booking", back_populates="centre_test", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CentreTest(id={self.id}, centre_id={self.centre_id}, test_id={self.test_id})>"
