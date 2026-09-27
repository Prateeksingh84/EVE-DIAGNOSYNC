from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    """Schema for initiating a payment."""

    booking_id: UUID = Field(
        ..., description="ID of the booking to pay for"
    )
    payment_method: str = Field(
        default="SIMULATED",
        max_length=50,
        description="Payment method",
    )


class PaymentResponse(BaseModel):
    """Schema for payment response."""

    id: UUID
    booking_id: UUID
    transaction_id: str
    amount: Decimal
    status: PaymentStatus
    payment_method: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookPayload(BaseModel):
    """Schema for incoming webhook events from the payment provider."""

    event_id: str = Field(
        ..., description="Unique event identifier for idempotency"
    )
    event_type: str = Field(
        ..., description="Type of the event, e.g., payment.success or payment.failed"
    )
    transaction_id: str = Field(
        ..., description="Transaction ID of the payment"
    )
    status: str = Field(
        ..., description="Payment status: SUCCESS or FAILED"
    )
    amount: Decimal = Field(..., description="Payment amount")
    booking_id: UUID = Field(
        ..., description="Related booking ID"
    )
    timestamp: Optional[datetime] = Field(
        None, description="Event timestamp"
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"SUCCESS", "FAILED"}
        if v.upper() not in allowed:
            raise ValueError(
                f"Invalid payment status. Must be one of: {allowed}"
            )
        return v.upper()

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed = {"payment.success", "payment.failed", "payment.refunded"}
        if v not in allowed:
            raise ValueError(
                f"Invalid event type. Must be one of: {allowed}"
            )
        return v


class WebhookResponse(BaseModel):
    """Schema for webhook processing response."""

    status: str
    message: str
    event_id: str
