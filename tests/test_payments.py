import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.diagnostic import DiagnosticCentre, DiagnosticTest, CentreTest
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus


@pytest_asyncio.fixture
async def pending_booking(
    db_session: AsyncSession, test_user: User
) -> Booking:
    """Create a pending booking for payment tests."""
    centre = DiagnosticCentre(
        id=uuid.uuid4(),
        name="Payment Test Lab",
        address="200 Pay Street",
        city="Delhi",
        state="Delhi",
        pincode="110001",
    )
    db_session.add(centre)

    test = DiagnosticTest(
        id=uuid.uuid4(),
        name="X-Ray",
        category="Radiology",
    )
    db_session.add(test)
    await db_session.flush()

    centre_test = CentreTest(
        id=uuid.uuid4(),
        centre_id=centre.id,
        test_id=test.id,
        price=1200.00,
    )
    db_session.add(centre_test)
    await db_session.flush()

    booking = Booking(
        id=uuid.uuid4(),
        booking_reference="EVE-TEST1234",
        user_id=test_user.id,
        centre_test_id=centre_test.id,
        appointment_datetime=datetime.now(timezone.utc) + timedelta(days=1),
        amount=1200.00,
        status=BookingStatus.PENDING,
    )
    db_session.add(booking)
    await db_session.flush()
    await db_session.refresh(booking)
    return booking


@pytest.mark.asyncio
class TestPayments:
    """Tests for payment endpoints."""

    async def test_create_payment(
        self,
        client: AsyncClient,
        auth_headers: dict,
        pending_booking: Booking,
    ):
        response = await client.post(
            "/api/v1/payments/",
            json={"booking_id": str(pending_booking.id)},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] in ["SUCCESS", "FAILED"]
        assert data["transaction_id"].startswith("TXN-")
        assert float(data["amount"]) == 1200.00

    async def test_create_payment_invalid_booking(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/payments/",
            json={"booking_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_create_payment_unauthenticated(
        self, client: AsyncClient, pending_booking: Booking
    ):
        response = await client.post(
            "/api/v1/payments/",
            json={"booking_id": str(pending_booking.id)},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestWebhook:
    """Tests for the payment webhook endpoint."""

    async def test_webhook_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        pending_booking: Booking,
    ):
        # First create a payment
        payment = Payment(
            id=uuid.uuid4(),
            booking_id=pending_booking.id,
            transaction_id="TXN-WEBHOOK001",
            amount=pending_booking.amount,
            status=PaymentStatus.PENDING,
        )
        db_session.add(payment)
        await db_session.flush()

        response = await client.post(
            "/api/v1/payments/webhook/",
            json={
                "event_id": "evt-unique-001",
                "event_type": "payment.success",
                "transaction_id": "TXN-WEBHOOK001",
                "status": "SUCCESS",
                "amount": 1200.00,
                "booking_id": str(pending_booking.id),
            },
            headers={
                "X-Webhook-Secret": settings.WEBHOOK_SECRET
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"

    async def test_webhook_idempotency(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        pending_booking: Booking,
    ):
        # Create a payment
        payment = Payment(
            id=uuid.uuid4(),
            booking_id=pending_booking.id,
            transaction_id="TXN-WEBHOOK002",
            amount=pending_booking.amount,
            status=PaymentStatus.PENDING,
        )
        db_session.add(payment)
        await db_session.flush()

        webhook_payload = {
            "event_id": "evt-duplicate-001",
            "event_type": "payment.success",
            "transaction_id": "TXN-WEBHOOK002",
            "status": "SUCCESS",
            "amount": 1200.00,
            "booking_id": str(pending_booking.id),
        }
        headers = {"X-Webhook-Secret": settings.WEBHOOK_SECRET}

        # First call
        resp1 = await client.post(
            "/api/v1/payments/webhook/",
            json=webhook_payload,
            headers=headers,
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "processed"

        # Duplicate call — should be idempotent
        resp2 = await client.post(
            "/api/v1/payments/webhook/",
            json=webhook_payload,
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "already_processed"

    async def test_webhook_invalid_secret(
        self, client: AsyncClient, pending_booking: Booking
    ):
        response = await client.post(
            "/api/v1/payments/webhook/",
            json={
                "event_id": "evt-invalid-secret",
                "event_type": "payment.success",
                "transaction_id": "TXN-INVALID",
                "status": "SUCCESS",
                "amount": 1200.00,
                "booking_id": str(pending_booking.id),
            },
            headers={"X-Webhook-Secret": "wrong-secret"},
        )
        assert response.status_code == 401

    async def test_webhook_missing_secret(
        self, client: AsyncClient, pending_booking: Booking
    ):
        response = await client.post(
            "/api/v1/payments/webhook/",
            json={
                "event_id": "evt-no-secret",
                "event_type": "payment.success",
                "transaction_id": "TXN-NOSECRET",
                "status": "SUCCESS",
                "amount": 1200.00,
                "booking_id": str(pending_booking.id),
            },
        )
        assert response.status_code == 401

    async def test_webhook_invalid_event_type(
        self, client: AsyncClient, pending_booking: Booking
    ):
        response = await client.post(
            "/api/v1/payments/webhook/",
            json={
                "event_id": "evt-bad-type",
                "event_type": "invalid.type",
                "transaction_id": "TXN-BADTYPE",
                "status": "SUCCESS",
                "amount": 1200.00,
                "booking_id": str(pending_booking.id),
            },
            headers={
                "X-Webhook-Secret": settings.WEBHOOK_SECRET
            },
        )
        assert response.status_code == 422
