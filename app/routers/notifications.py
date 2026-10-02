import math
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/",
    summary="List user notifications",
    description="Retrieve audit log of simulated email/SMS notifications dispatched to the current user.",
)
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    notifications, total = await notification_service.get_user_notifications(
        db, current_user.id, offset, page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    items = [
        {
            "id": str(n.id),
            "booking_id": str(n.booking_id) if n.booking_id else None,
            "channel": n.channel.value,
            "recipient": n.recipient,
            "subject": n.subject,
            "body": n.body,
            "status": n.status.value,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications
    ]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
