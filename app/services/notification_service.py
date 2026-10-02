import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.user import User

logger = structlog.get_logger(__name__)


async def create_and_send_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    recipient: str,
    subject: str,
    body: str,
    booking_id: Optional[uuid.UUID] = None,
    channel: NotificationChannel = NotificationChannel.EMAIL,
) -> Notification:
    """
    Log and dispatch a simulated notification (Email/SMS).
    In production, this delegates to an SMTP, SendGrid, or AWS SES gateway.
    """
    notification = Notification(
        user_id=user_id,
        booking_id=booking_id,
        channel=channel,
        recipient=recipient,
        subject=subject,
        body=body,
        status=NotificationStatus.SENT,
    )
    db.add(notification)
    await db.flush()

    logger.info(
        "notification_dispatched",
        notification_id=str(notification.id),
        channel=channel.value,
        recipient=recipient,
        subject=subject,
        booking_id=str(booking_id) if booking_id else None,
    )
    return notification


async def notify_booking_created(db: AsyncSession, booking: Booking, user: User) -> None:
    """Send booking created / pending payment notification."""
    centre_name = booking.centre_test.centre.name if booking.centre_test and booking.centre_test.centre else "Selected Centre"
    test_name = booking.centre_test.test.name if booking.centre_test and booking.centre_test.test else "Diagnostic Test"

    subject = f"Booking Created: {test_name} at {centre_name} (Ref: {booking.booking_reference})"
    body = (
        f"Dear {user.full_name},\n\n"
        f"Your booking for '{test_name}' at {centre_name} on "
        f"{booking.appointment_datetime.strftime('%d %b %Y at %I:%M %p')} has been created.\n\n"
        f"Amount: INR {booking.amount:,.2f}\n"
        f"Current Status: PENDING PAYMENT\n\n"
        f"Please complete payment within 30 minutes to confirm your slot.\n\n"
        f"Warm regards,\nEVE Healthcare Diagnostics Team"
    )
    await create_and_send_notification(
        db=db,
        user_id=user.id,
        recipient=user.email,
        subject=subject,
        body=body,
        booking_id=booking.id,
        channel=NotificationChannel.EMAIL,
    )


async def notify_payment_success(db: AsyncSession, booking: Booking, payment: Payment, user: User) -> None:
    """Send payment success & appointment confirmation notification."""
    test_name = booking.centre_test.test.name if booking.centre_test and booking.centre_test.test else "Diagnostic Test"

    subject = f"Payment Confirmed: {booking.booking_reference} for {test_name}"
    body = (
        f"Dear {user.full_name},\n\n"
        f"We have received your payment of INR {payment.amount:,.2f} (Txn: {payment.transaction_id}).\n"
        f"Your appointment is now CONFIRMED for {booking.appointment_datetime.strftime('%d %b %Y at %I:%M %p')}.\n\n"
        f"You can download your official PDF invoice and receipt directly from your dashboard.\n\n"
        f"Preparation Note: Please fast for 10-12 hours before test time if your test requires blood draw.\n\n"
        f"Thank you for choosing EVE Healthcare!"
    )
    await create_and_send_notification(
        db=db,
        user_id=user.id,
        recipient=user.email,
        subject=subject,
        body=body,
        booking_id=booking.id,
        channel=NotificationChannel.EMAIL,
    )


async def notify_payment_failed(db: AsyncSession, booking: Booking, payment: Payment, user: User) -> None:
    """Send payment failure alert."""
    subject = f"Payment Failed for Booking {booking.booking_reference}"
    body = (
        f"Dear {user.full_name},\n\n"
        f"Your payment attempt for booking {booking.booking_reference} (Txn: {payment.transaction_id}) has FAILED.\n"
        f"Amount: INR {payment.amount:,.2f}\n\n"
        f"Please visit your EVE Healthcare dashboard to retry payment before your slot expires.\n\n"
        f"EVE Healthcare Support"
    )
    await create_and_send_notification(
        db=db,
        user_id=user.id,
        recipient=user.email,
        subject=subject,
        body=body,
        booking_id=booking.id,
        channel=NotificationChannel.EMAIL,
    )


async def notify_booking_cancelled(db: AsyncSession, booking: Booking, user: User) -> None:
    """Send booking cancellation notification."""
    subject = f"Booking Cancelled: {booking.booking_reference}"
    body = (
        f"Dear {user.full_name},\n\n"
        f"Your booking {booking.booking_reference} scheduled for "
        f"{booking.appointment_datetime.strftime('%d %b %Y at %I:%M %p')} has been cancelled as requested.\n\n"
        f"EVE Healthcare Team"
    )
    await create_and_send_notification(
        db=db,
        user_id=user.id,
        recipient=user.email,
        subject=subject,
        body=body,
        booking_id=booking.id,
        channel=NotificationChannel.EMAIL,
    )


async def get_user_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 20,
) -> Tuple[List[Notification], int]:
    """Retrieve user notifications with total count."""
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    notifications = list(result.scalars().all())

    count_result = await db.execute(
        select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    )
    total = count_result.scalar() or 0
    return notifications, total
