import secrets
import string
from datetime import datetime, timezone, timedelta, date, time
from typing import List, Optional, Tuple, Dict, Any
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.models.booking import Booking, BookingStatus
from app.models.diagnostic import CentreTest
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.services import notification_service
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
    ConflictException,
)

logger = structlog.get_logger(__name__)

MAX_SLOT_CAPACITY = 5  # Max concurrent bookings allowed per 30-minute window per centre


def _generate_booking_reference() -> str:
    """Generate a unique booking reference like EVE-XXXXXXXX."""
    chars = string.ascii_uppercase + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(8))
    return f"EVE-{random_part}"


async def create_booking(
    db: AsyncSession,
    user_id: uuid.UUID,
    booking_data: BookingCreate,
) -> Booking:
    """
    Create a new diagnostic test booking.
    Guarded against:
    1. Double-booking race conditions by the same user.
    2. Over-booking past the centre's maximum slot capacity.
    """
    # Validate centre_test exists and is available
    result = await db.execute(
        select(CentreTest)
        .options(
            selectinload(CentreTest.centre),
            selectinload(CentreTest.test),
        )
        .where(CentreTest.id == booking_data.centre_test_id)
    )
    centre_test = result.scalar_one_or_none()

    if not centre_test:
        raise NotFoundException(
            resource="Centre test",
            resource_id=str(booking_data.centre_test_id),
        )

    if not centre_test.is_available:
        raise BadRequestException(
            detail="This test is currently not available at the selected centre"
        )

    if not centre_test.centre.is_active:
        raise BadRequestException(
            detail="The selected diagnostic centre is currently inactive"
        )

    # Slot Window (30-minute interval around appointment)
    slot_start = booking_data.appointment_datetime - timedelta(minutes=15)
    slot_end = booking_data.appointment_datetime + timedelta(minutes=15)

    # 1. Double-Booking Prevention: Same user cannot book the same test at overlapping times
    dup_check = await db.execute(
        select(Booking).where(
            Booking.user_id == user_id,
            Booking.centre_test_id == centre_test.id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.appointment_datetime >= slot_start,
            Booking.appointment_datetime <= slot_end,
        )
    )
    if dup_check.scalar_one_or_none():
        raise ConflictException(
            detail="You already have an active booking scheduled for this test around this time."
        )

    # 2. Centre Capacity Lock / Slot Over-booking Check
    capacity_check = await db.execute(
        select(func.count(Booking.id))
        .join(CentreTest, Booking.centre_test_id == CentreTest.id)
        .where(
            CentreTest.centre_id == centre_test.centre_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.appointment_datetime >= slot_start,
            Booking.appointment_datetime <= slot_end,
        )
    )
    current_bookings = capacity_check.scalar() or 0

    if current_bookings >= MAX_SLOT_CAPACITY:
        raise ConflictException(
            detail=f"This time slot is fully booked ({current_bookings}/{MAX_SLOT_CAPACITY} capacity reached). "
            f"Please select an alternative slot."
        )

    # Generate unique booking reference
    booking_reference = _generate_booking_reference()

    booking = Booking(
        booking_reference=booking_reference,
        user_id=user_id,
        centre_test_id=centre_test.id,
        appointment_datetime=booking_data.appointment_datetime,
        amount=centre_test.price,
        status=BookingStatus.PENDING,
    )
    db.add(booking)
    await db.flush()
    await db.refresh(booking)

    # Load user and trigger simulated email/SMS notification
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        try:
            await notification_service.notify_booking_created(db, booking, user)
        except Exception as e:
            logger.warning("notification_dispatch_failed", error=str(e))

    logger.info(
        "booking_created",
        booking_id=str(booking.id),
        booking_ref=booking.booking_reference,
        user_id=str(user_id),
        amount=str(booking.amount),
    )
    return booking


async def get_booking(
    db: AsyncSession,
    booking_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = None,
) -> Booking:
    """Retrieve a booking by ID, optionally filtering by user."""
    query = (
        select(Booking)
        .options(
            selectinload(Booking.centre_test).selectinload(CentreTest.test),
            selectinload(Booking.centre_test).selectinload(CentreTest.centre),
            selectinload(Booking.payments),
        )
        .where(Booking.id == booking_id)
    )

    if user_id:
        query = query.where(Booking.user_id == user_id)

    result = await db.execute(query)
    booking = result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(
            resource="Booking", resource_id=str(booking_id)
        )

    return booking


async def get_user_bookings(
    db: AsyncSession,
    user_id: uuid.UUID,
    offset: int = 0,
    limit: int = 20,
    status_filter: Optional[BookingStatus] = None,
) -> Tuple[List[Booking], int]:
    """Retrieve all bookings for a user with pagination."""
    query = (
        select(Booking)
        .options(
            selectinload(Booking.centre_test).selectinload(CentreTest.test),
            selectinload(Booking.centre_test).selectinload(CentreTest.centre),
            selectinload(Booking.payments),
        )
        .where(Booking.user_id == user_id)
    )

    count_query = select(func.count()).select_from(Booking).where(
        Booking.user_id == user_id
    )

    if status_filter:
        query = query.where(Booking.status == status_filter)
        count_query = count_query.where(Booking.status == status_filter)

    query = query.order_by(Booking.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    bookings = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return bookings, total


async def cancel_booking(
    db: AsyncSession,
    booking_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Booking:
    """Cancel a booking. Only PENDING bookings can be cancelled."""
    booking = await get_booking(db, booking_id)

    # Verify ownership
    if booking.user_id != user_id:
        raise ForbiddenException(
            detail="You do not have permission to cancel this booking"
        )

    if booking.status != BookingStatus.PENDING:
        raise BadRequestException(
            detail=f"Cannot cancel a booking with status '{booking.status.value}'. "
            f"Only PENDING bookings can be cancelled."
        )

    booking.status = BookingStatus.CANCELLED
    await db.flush()
    await db.refresh(booking)

    # Send cancellation notification
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user:
        try:
            await notification_service.notify_booking_cancelled(db, booking, user)
        except Exception as e:
            logger.warning("notification_dispatch_failed", error=str(e))

    logger.info(
        "booking_cancelled",
        booking_id=str(booking.id),
        booking_ref=booking.booking_reference,
        user_id=str(user_id),
    )
    return booking


async def update_booking_status(
    db: AsyncSession,
    booking_id: uuid.UUID,
    new_status: BookingStatus,
) -> Booking:
    """Update a booking's status (used internally by payment processing)."""
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise NotFoundException(
            resource="Booking", resource_id=str(booking_id)
        )

    old_status = booking.status
    booking.status = new_status
    await db.flush()
    await db.refresh(booking)

    logger.info(
        "booking_status_updated",
        booking_id=str(booking.id),
        old_status=old_status.value,
        new_status=new_status.value,
    )
    return booking


async def get_available_slots(
    db: AsyncSession,
    centre_test_id: uuid.UUID,
    target_date: date,
) -> List[Dict[str, Any]]:
    """
    Calculate real-time appointment slot availability for a test at a centre.
    Generates 30-minute intervals between 08:00 AM and 06:00 PM.
    """
    # Verify centre_test
    result = await db.execute(
        select(CentreTest).where(CentreTest.id == centre_test_id)
    )
    ct = result.scalar_one_or_none()
    if not ct:
        raise NotFoundException(resource="Centre test", resource_id=str(centre_test_id))

    slots = []
    # Slots from 08:00 to 18:00
    start_hour = 8
    end_hour = 18

    # Query all active bookings for this centre on target_date
    day_start = datetime.combine(target_date, time(0, 0, 0), tzinfo=timezone.utc)
    day_end = datetime.combine(target_date, time(23, 59, 59), tzinfo=timezone.utc)

    bookings_result = await db.execute(
        select(Booking.appointment_datetime)
        .join(CentreTest, Booking.centre_test_id == CentreTest.id)
        .where(
            CentreTest.centre_id == ct.centre_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.appointment_datetime >= day_start,
            Booking.appointment_datetime <= day_end,
        )
    )
    active_times = [
        r[0].replace(tzinfo=timezone.utc) if r[0].tzinfo is None else r[0]
        for r in bookings_result.all()
    ]

    current_dt = datetime.combine(target_date, time(start_hour, 0), tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, time(end_hour, 0), tzinfo=timezone.utc)

    now_utc = datetime.now(timezone.utc)

    while current_dt <= end_dt:
        # Count overlapping bookings (+/- 15 mins)
        w_start = current_dt - timedelta(minutes=15)
        w_end = current_dt + timedelta(minutes=15)
        booked_count = sum(1 for bt in active_times if w_start <= bt <= w_end)

        available_capacity = max(0, MAX_SLOT_CAPACITY - booked_count)
        is_in_past = current_dt <= now_utc
        is_available = (available_capacity > 0) and not is_in_past

        slots.append({
            "slot_time": current_dt.strftime("%H:%M"),
            "slot_datetime": current_dt.isoformat(),
            "max_capacity": MAX_SLOT_CAPACITY,
            "booked_count": booked_count,
            "available_capacity": available_capacity,
            "is_available": is_available,
        })
        current_dt += timedelta(minutes=30)

    return slots
