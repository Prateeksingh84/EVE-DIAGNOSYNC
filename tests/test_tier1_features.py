import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient

from app.models.diagnostic import DiagnosticCentre, DiagnosticTest, CentreTest
from app.models.user import User


class TestTokenRotation:
    """Test suite for refresh token rotation and replay attack mitigation."""

    @pytest.mark.asyncio
    async def test_refresh_token_rotation_and_replay_detection(
        self, client: AsyncClient, test_user: User
    ):
        # 1. Login to obtain access and rotating refresh token
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "TestPass123!"},
        )
        assert login_res.status_code == 200
        data = login_res.json()
        token_1 = data["refresh_token"]

        # 2. Rotate token
        rotate_res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": token_1},
        )
        assert rotate_res.status_code == 200
        rotate_data = rotate_res.json()
        token_2 = rotate_data["refresh_token"]
        assert token_1 != token_2

        # 3. Replay attack: reusing token_1 must be rejected with 401
        replay_res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": token_1},
        )
        assert replay_res.status_code == 401
        assert "Refresh token reuse detected" in replay_res.json()["detail"]


class TestSlotConflictAndBooking:
    """Test suite for slot capacity and double-booking conflict guards."""

    @pytest.mark.asyncio
    async def test_slot_availability_and_conflict_guard(
        self,
        client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        db_session,
    ):
        # Create centre and test
        centre = DiagnosticCentre(
            name="Conflict Test Centre",
            address="100 Tech Park",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
        )
        test = DiagnosticTest(
            name="Advanced Genetic Screen",
            description="DNA screening",
            category="Genetics",
        )
        db_session.add_all([centre, test])
        await db_session.flush()

        centre_test = CentreTest(
            centre_id=centre.id,
            test_id=test.id,
            price=2500.00,
            is_available=True,
        )
        db_session.add(centre_test)
        await db_session.commit()

        # Check slot availability
        target_date = (datetime.now(timezone.utc) + timedelta(days=5)).date()
        slots_res = await client.get(
            f"/api/v1/bookings/slots/availability?centre_test_id={centre_test.id}&booking_date={target_date.isoformat()}"
        )
        assert slots_res.status_code == 200
        slots = slots_res.json()["slots"]
        assert len(slots) > 0

        # Book a slot
        appt_time = (datetime.now(timezone.utc) + timedelta(days=5)).replace(
            hour=11, minute=0, second=0, microsecond=0
        )
        book_res = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "centre_test_id": str(centre_test.id),
                "appointment_datetime": appt_time.isoformat(),
            },
        )
        assert book_res.status_code == 201
        booking_id = book_res.json()["id"]

        # Duplicate booking attempt around same time window must return 409 Conflict
        dup_res = await client.post(
            "/api/v1/bookings/",
            headers=auth_headers,
            json={
                "centre_test_id": str(centre_test.id),
                "appointment_datetime": appt_time.isoformat(),
            },
        )
        assert dup_res.status_code == 409
        assert "already have an active booking" in dup_res.json()["detail"]

        # Test PDF receipt generation
        receipt_res = await client.get(
            f"/api/v1/bookings/{booking_id}/receipt",
            headers=auth_headers,
        )
        assert receipt_res.status_code == 200
        assert receipt_res.headers["content-type"] == "application/pdf"
        assert len(receipt_res.content) > 500


class TestAnalyticsAndNotifications:
    """Test suite for notification audit trail and admin analytics."""

    @pytest.mark.asyncio
    async def test_notifications_and_analytics(
        self,
        client: AsyncClient,
        test_user: User,
        admin_user: User,
        auth_headers: dict,
        admin_auth_headers: dict,
    ):
        # 1. User notifications
        notif_res = await client.get(
            "/api/v1/notifications/",
            headers=auth_headers,
        )
        assert notif_res.status_code == 200
        assert "items" in notif_res.json()

        # 2. Regular user cannot access admin analytics
        forbidden_res = await client.get(
            "/api/v1/analytics/overview",
            headers=auth_headers,
        )
        assert forbidden_res.status_code == 403

        # 3. Admin can access overview analytics
        admin_res = await client.get(
            "/api/v1/analytics/overview",
            headers=admin_auth_headers,
        )
        assert admin_res.status_code == 200
        data = admin_res.json()
        assert "kpis" in data
        assert "total_bookings" in data["kpis"]

        # 4. Admin CSV export
        csv_res = await client.get(
            "/api/v1/analytics/export",
            headers=admin_auth_headers,
        )
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers["content-type"]
        assert "Booking Reference" in csv_res.text
