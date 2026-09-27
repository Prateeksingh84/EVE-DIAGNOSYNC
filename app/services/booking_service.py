import secrets
import string
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.models.booking import Booking, BookingStatus
from app.models.diagnostic import CentreTest
from app.schemas.booking import BookingCreate
from app.utils.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException,
)

logger = structlog.get_logger(__name__)


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
    """Create a new diagnostic test booking."""
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
    total = count_result.scalar()

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
