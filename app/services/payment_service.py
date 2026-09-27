import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus, WebhookEvent
from app.schemas.payment import PaymentCreate, WebhookPayload
from app.services.booking_service import update_booking_status
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException,
)

logger = structlog.get_logger(__name__)


def _simulate_payment_result() -> PaymentStatus:
    """Simulate a payment gateway result. 80% success rate."""
    return (
        PaymentStatus.SUCCESS
        if random.random() < 0.8
        else PaymentStatus.FAILED
    )


async def create_payment(
    db: AsyncSession,
    payment_data: PaymentCreate,
    user_id: uuid.UUID,
) -> Payment:
    """Process a simulated payment for a booking."""
    # Validate booking exists and belongs to user
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.payments))
        .where(Booking.id == payment_data.booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(
            resource="Booking",
            resource_id=str(payment_data.booking_id),
        )

    # Verify ownership
    if booking.user_id != user_id:
        raise BadRequestException(
            detail="You do not have permission to pay for this booking"
        )

    # Check booking is in PENDING state
    if booking.status != BookingStatus.PENDING:
        raise BadRequestException(
            detail=f"Cannot process payment for a booking with status '{booking.status.value}'. "
            f"Only PENDING bookings can be paid for."
        )

    # Check for existing successful payment
    existing_success = any(
        p.status == PaymentStatus.SUCCESS for p in booking.payments
    )
    if existing_success:
        raise ConflictException(
            detail="A successful payment already exists for this booking"
        )

    # Generate transaction ID
    transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    # Simulate payment processing
    payment_result = _simulate_payment_result()

    payment = Payment(
        booking_id=booking.id,
        transaction_id=transaction_id,
        amount=booking.amount,
        status=payment_result,
        payment_method=payment_data.payment_method,
    )
    db.add(payment)

    # Update booking status based on payment result
    if payment_result == PaymentStatus.SUCCESS:
        booking.status = BookingStatus.CONFIRMED
        logger.info(
            "payment_success",
            transaction_id=transaction_id,
            booking_id=str(booking.id),
            amount=str(booking.amount),
        )
    else:
        booking.status = BookingStatus.FAILED
        logger.warning(
            "payment_failed",
            transaction_id=transaction_id,
            booking_id=str(booking.id),
            amount=str(booking.amount),
        )

    await db.flush()
    await db.refresh(payment)

    return payment


async def process_webhook(
    db: AsyncSession,
    webhook_data: WebhookPayload,
) -> dict:
    """
    Process an incoming payment webhook event.
    This is idempotent - duplicate events are safely ignored.
    """
    # Check if this event has already been processed (idempotency)
    existing_event = await db.execute(
        select(WebhookEvent).where(
            WebhookEvent.event_id == webhook_data.event_id
        )
    )
    existing = existing_event.scalar_one_or_none()

    if existing:
        if existing.processed:
            logger.info(
                "webhook_duplicate_ignored",
                event_id=webhook_data.event_id,
            )
            return {
                "status": "already_processed",
                "message": "This event has already been processed",
                "event_id": webhook_data.event_id,
            }
        # Event exists but wasn't processed - continue processing
    else:
        # Record the event for idempotency tracking
        webhook_event = WebhookEvent(
            event_id=webhook_data.event_id,
            event_type=webhook_data.event_type,
            payload=webhook_data.model_dump(mode="json"),
        )
        db.add(webhook_event)
        await db.flush()
        existing = webhook_event

    # Find the payment by transaction_id
    payment_result = await db.execute(
        select(Payment).where(
            Payment.transaction_id == webhook_data.transaction_id
        )
    )
    payment = payment_result.scalar_one_or_none()

    if not payment:
        logger.warning(
            "webhook_payment_not_found",
            event_id=webhook_data.event_id,
            transaction_id=webhook_data.transaction_id,
        )
        # Still mark as processed to prevent retry loops
        existing.processed = True
        existing.processed_at = datetime.now(timezone.utc)
        await db.flush()
        return {
            "status": "error",
            "message": f"Payment with transaction ID '{webhook_data.transaction_id}' not found",
            "event_id": webhook_data.event_id,
        }

    # Validate booking_id matches
    if payment.booking_id != webhook_data.booking_id:
        logger.warning(
            "webhook_booking_mismatch",
            event_id=webhook_data.event_id,
            expected_booking=str(payment.booking_id),
            received_booking=str(webhook_data.booking_id),
        )
        existing.processed = True
        existing.processed_at = datetime.now(timezone.utc)
        await db.flush()
        return {
            "status": "error",
            "message": "Booking ID mismatch",
            "event_id": webhook_data.event_id,
        }

    # Update payment status
    new_payment_status = (
        PaymentStatus.SUCCESS
        if webhook_data.status == "SUCCESS"
        else PaymentStatus.FAILED
    )
    payment.status = new_payment_status

    # Update booking status
    new_booking_status = (
        BookingStatus.CONFIRMED
        if new_payment_status == PaymentStatus.SUCCESS
        else BookingStatus.FAILED
    )
    await update_booking_status(db, payment.booking_id, new_booking_status)

    # Mark webhook event as processed
    existing.processed = True
    existing.processed_at = datetime.now(timezone.utc)
    await db.flush()

    logger.info(
        "webhook_processed",
        event_id=webhook_data.event_id,
        transaction_id=webhook_data.transaction_id,
        payment_status=new_payment_status.value,
        booking_status=new_booking_status.value,
    )

    return {
        "status": "processed",
        "message": f"Payment {new_payment_status.value}, booking {new_booking_status.value}",
        "event_id": webhook_data.event_id,
    }


async def get_payment(
    db: AsyncSession,
    payment_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
) -> Payment:
    """Retrieve a payment by ID."""
    query = (
        select(Payment)
        .options(selectinload(Payment.booking))
        .where(Payment.id == payment_id)
    )

    result = await db.execute(query)
    payment = result.scalar_one_or_none()

    if not payment:
        raise NotFoundException(
            resource="Payment", resource_id=str(payment_id)
        )

    # If user_id provided, verify ownership via booking
    if user_id and payment.booking.user_id != user_id:
        raise NotFoundException(
            resource="Payment", resource_id=str(payment_id)
        )

    return payment
