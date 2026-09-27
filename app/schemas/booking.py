from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    """Schema for creating a booking."""

    centre_test_id: UUID = Field(
        ..., description="ID of the centre-test association"
    )
    appointment_datetime: datetime = Field(
        ..., description="Desired appointment date and time"
    )

    @field_validator("appointment_datetime")
    @classmethod
    def validate_appointment_in_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        if v <= datetime.now(timezone.utc):
            raise ValueError("Appointment datetime must be in the future")
        return v


class BookingResponse(BaseModel):
    """Schema for booking response."""

    id: UUID
    booking_reference: str
    user_id: UUID
    centre_test_id: UUID
    appointment_datetime: datetime
    amount: Decimal
    status: BookingStatus
    created_at: datetime
    updated_at: datetime

    # Nested details
    centre_name: Optional[str] = None
    test_name: Optional[str] = None

    model_config = {"from_attributes": True}
