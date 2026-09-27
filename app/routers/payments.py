from typing import Annotated
from uuid import UUID
import hashlib
import hmac

from fastapi import APIRouter, Depends, Header, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    WebhookPayload,
    WebhookResponse,
)
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post(
    "/",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process a simulated payment",
    description="Initiate a simulated payment for a booking. The result is randomly SUCCESS or FAILED.",
)
async def create_payment(
    payment_data: PaymentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    payment = await payment_service.create_payment(
        db, payment_data, current_user.id
    )
    return payment


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment details",
    description="Retrieve details of a specific payment.",
)
async def get_payment(
    payment_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    payment = await payment_service.get_payment(
        db, payment_id, current_user.id
    )
    return payment


@router.post(
    "/webhook/",
    response_model=WebhookResponse,
    summary="Payment webhook endpoint",
    description=(
        "Receive payment status updates from the payment provider. "
        "This endpoint is idempotent — duplicate events are safely ignored."
    ),
)
async def payment_webhook(
    webhook_data: WebhookPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_webhook_secret: str = Header(
        default=None,
        alias="X-Webhook-Secret",
        description="Webhook authentication secret",
    ),
):
    # Verify webhook secret
    if x_webhook_secret != settings.WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )

    result = await payment_service.process_webhook(db, webhook_data)
    return WebhookResponse(**result)
