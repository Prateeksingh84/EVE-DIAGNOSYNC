import uuid
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.diagnostic import DiagnosticCentre, DiagnosticTest, CentreTest


@pytest_asyncio.fixture
async def setup_centre_test(
    db_session: AsyncSession,
) -> CentreTest:
    """Create a centre with a test for booking tests."""
    centre = DiagnosticCentre(
        id=uuid.uuid4(),
        name="Test Health Lab",
        address="100 Test Street",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
    )
    db_session.add(centre)

    test = DiagnosticTest(
        id=uuid.uuid4(),
        name="Complete Blood Count",
        description="CBC Test",
        category="Hematology",
    )
    db_session.add(test)
    await db_session.flush()

    centre_test = CentreTest(
        id=uuid.uuid4(),
        centre_id=centre.id,
        test_id=test.id,
        price=500.00,
        is_available=True,
    )
    db_session.add(centre_test)
    await db_session.flush()
    await db_session.refresh(centre_test)
    return centre_test


import pytest_asyncio


@pytest.mark.asyncio
class TestBookings:
    """Tests for the booking endpoints."""

    async def test_create_booking(
        self,
        client: AsyncClient,
        auth_headers: dict,
        setup_centre_test: CentreTest,
    ):
        future_dt = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat()

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "centre_test_id": str(setup_centre_test.id),
                "appointment_datetime": future_dt,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PENDING"
        assert data["booking_reference"].startswith("EVE-")
        assert float(data["amount"]) == 500.00

    async def test_create_booking_past_datetime(
        self,
        client: AsyncClient,
        auth_headers: dict,
        setup_centre_test: CentreTest,
    ):
        past_dt = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).isoformat()

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "centre_test_id": str(setup_centre_test.id),
                "appointment_datetime": past_dt,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_create_booking_invalid_centre_test(
        self, client: AsyncClient, auth_headers: dict
    ):
        future_dt = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat()

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "centre_test_id": str(uuid.uuid4()),
                "appointment_datetime": future_dt,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_create_booking_unauthenticated(
        self, client: AsyncClient, setup_centre_test: CentreTest
    ):
        future_dt = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat()

        response = await client.post(
            "/api/v1/bookings/",
            json={
                "centre_test_id": str(setup_centre_test.id),
                "appointment_datetime": future_dt,
            },
        )
        assert response.status_code == 403

    async def test_list_bookings(
        self,
        client: AsyncClient,
        auth_headers: dict,
        setup_centre_test: CentreTest,
    ):
        # Create a booking first
        future_dt = (
            datetime.now(timezone.utc) + timedelta(days=2)
        ).isoformat()
        await client.post(
            "/api/v1/bookings/",
            json={
                "centre_test_id": str(setup_centre_test.id),
                "appointment_datetime": future_dt,
            },
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/bookings/", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1

    async def test_cancel_booking(
        self,
        client: AsyncClient,
        auth_headers: dict,
        setup_centre_test: CentreTest,
    ):
        # Create a booking
        future_dt = (
            datetime.now(timezone.utc) + timedelta(days=3)
        ).isoformat()
        create_resp = await client.post(
            "/api/v1/bookings/",
            json={
                "centre_test_id": str(setup_centre_test.id),
                "appointment_datetime": future_dt,
            },
            headers=auth_headers,
        )
        booking_id = create_resp.json()["id"]

        # Cancel it
        response = await client.post(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"

    async def test_get_booking_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/bookings/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
