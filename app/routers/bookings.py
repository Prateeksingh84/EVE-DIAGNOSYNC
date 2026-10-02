from datetime import date
import math
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.booking import BookingStatus
from app.schemas.booking import BookingCreate, BookingResponse
from app.services import booking_service
from app.services.pdf_service import generate_booking_receipt_pdf
from app.utils.pagination import PaginatedResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _enrich_booking_response(booking) -> dict:
    """Add nested centre and test names to booking response."""
    data = BookingResponse.model_validate(booking).model_dump(mode="json")
    if booking.centre_test:
        if booking.centre_test.centre:
            data["centre_name"] = booking.centre_test.centre.name
        if booking.centre_test.test:
            data["test_name"] = booking.centre_test.test.name
    return data


@router.post(
    "/",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    description="Book a diagnostic test at a specific centre. Includes conflict detection and slot capacity guard.",
)
async def create_booking(
    booking_data: BookingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    booking = await booking_service.create_booking(
        db, current_user.id, booking_data
    )
    # Reload with full relationships
    booking = await booking_service.get_booking(
        db, booking.id, current_user.id
    )
    return _enrich_booking_response(booking)


@router.get(
    "/slots/availability",
    summary="Check slot availability",
    description="Get real-time appointment time slots with remaining capacities for a test on a specific date.",
)
async def check_slot_availability(
    centre_test_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    booking_date: date = Query(..., description="Target date YYYY-MM-DD"),
):
    slots = await booking_service.get_available_slots(
        db, centre_test_id, booking_date
    )
    return {
        "centre_test_id": centre_test_id,
        "date": booking_date.isoformat(),
        "total_slots": len(slots),
        "slots": slots,
    }


@router.get(
    "/",
    response_model=PaginatedResponse[BookingResponse],
    summary="List user bookings",
    description="Retrieve all bookings for the authenticated user.",
)
async def list_bookings(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[BookingStatus] = Query(
        default=None, alias="status", description="Filter by booking status"
    ),
):
    offset = (page - 1) * page_size
    bookings, total = await booking_service.get_user_bookings(
        db, current_user.id, offset, page_size, status_filter
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "items": [_enrich_booking_response(b) for b in bookings],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


@router.get(
    "/{booking_id}/receipt",
    summary="Download PDF Receipt / Invoice",
    description="Generate and download an official hospital-grade PDF invoice and booking receipt.",
)
async def download_receipt(
    booking_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Verify booking exists and belongs to user (or user is admin)
    user_filter = None if current_user.is_admin else current_user.id
    booking = await booking_service.get_booking(db, booking_id, user_filter)

    pdf_buffer = generate_booking_receipt_pdf(
        booking=booking,
        user_email=current_user.email,
        user_name=current_user.full_name,
    )

    filename = f"receipt-{booking.booking_reference}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get booking details",
    description="Retrieve details of a specific booking.",
)
async def get_booking(
    booking_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    booking = await booking_service.get_booking(
        db, booking_id, current_user.id
    )
    return _enrich_booking_response(booking)


@router.post(
    "/{booking_id}/cancel",
    response_model=BookingResponse,
    summary="Cancel a booking",
    description="Cancel a pending booking. Only PENDING bookings can be cancelled.",
)
async def cancel_booking(
    booking_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    booking = await booking_service.cancel_booking(
        db, booking_id, current_user.id
    )
    booking = await booking_service.get_booking(
        db, booking.id, current_user.id
    )
    return _enrich_booking_response(booking)
