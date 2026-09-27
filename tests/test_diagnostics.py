import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestDiagnosticCentres:
    """Tests for diagnostic centres endpoints."""

    async def test_create_centre_as_admin(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/diagnostics/centres",
            json={
                "name": "Apollo Diagnostics",
                "address": "123 Health Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001",
                "phone": "+912212345678",
                "email": "apollo@example.com",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Apollo Diagnostics"
        assert data["city"] == "Mumbai"

    async def test_create_centre_as_regular_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/diagnostics/centres",
            json={
                "name": "Test Centre",
                "address": "456 Lab Lane",
                "city": "Delhi",
                "state": "Delhi",
                "pincode": "110001",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_create_centre_unauthenticated(
        self, client: AsyncClient
    ):
        response = await client.post(
            "/api/v1/diagnostics/centres",
            json={
                "name": "Test Centre",
                "address": "456 Lab Lane",
                "city": "Delhi",
                "state": "Delhi",
                "pincode": "110001",
            },
        )
        assert response.status_code == 403

    async def test_list_centres(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        # Create a centre first
        await client.post(
            "/api/v1/diagnostics/centres",
            json={
                "name": "HealthLab",
                "address": "789 Test Ave",
                "city": "Bangalore",
                "state": "Karnataka",
                "pincode": "560001",
            },
            headers=admin_auth_headers,
        )

        response = await client.get("/api/v1/diagnostics/centres")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_get_centre_not_found(self, client: AsyncClient):
        import uuid
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/diagnostics/centres/{fake_id}"
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDiagnosticTests:
    """Tests for diagnostic tests endpoints."""

    async def test_create_test_as_admin(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        response = await client.post(
            "/api/v1/diagnostics/tests",
            json={
                "name": "Complete Blood Count",
                "description": "A complete blood count test",
                "category": "Hematology",
            },
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Complete Blood Count"
        assert data["category"] == "Hematology"

    async def test_list_tests(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        # Create a test first
        await client.post(
            "/api/v1/diagnostics/tests",
            json={
                "name": "Lipid Panel",
                "description": "Cholesterol test",
                "category": "Biochemistry",
            },
            headers=admin_auth_headers,
        )

        response = await client.get("/api/v1/diagnostics/tests")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1


@pytest.mark.asyncio
class TestCentreTests:
    """Tests for centre-test association endpoints."""

    async def test_add_test_to_centre(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        # Create centre
        centre_resp = await client.post(
            "/api/v1/diagnostics/centres",
            json={
                "name": "PathLab Plus",
                "address": "101 Lab St",
                "city": "Pune",
                "state": "Maharashtra",
                "pincode": "411001",
            },
            headers=admin_auth_headers,
        )
        centre_id = centre_resp.json()["id"]

        # Create test
        test_resp = await client.post(
            "/api/v1/diagnostics/tests",
            json={
                "name": "Blood Sugar",
                "description": "Fasting blood sugar test",
                "category": "Biochemistry",
            },
            headers=admin_auth_headers,
        )
        test_id = test_resp.json()["id"]

        # Add test to centre
        response = await client.post(
            f"/api/v1/diagnostics/centres/{centre_id}/tests",
            json={"test_id": test_id, "price": 350.00},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert float(data["price"]) == 350.00

    async def test_add_duplicate_test_to_centre(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        # Create centre and test
        centre_resp = await client.post(
            "/api/v1/diagnostics/centres",
            json={
                "name": "Unique Lab",
                "address": "202 Test Rd",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "pincode": "600001",
            },
            headers=admin_auth_headers,
        )
        centre_id = centre_resp.json()["id"]

        test_resp = await client.post(
            "/api/v1/diagnostics/tests",
            json={
                "name": "Thyroid Panel",
                "category": "Endocrinology",
            },
            headers=admin_auth_headers,
        )
        test_id = test_resp.json()["id"]

        # First add
        await client.post(
            f"/api/v1/diagnostics/centres/{centre_id}/tests",
            json={"test_id": test_id, "price": 500.00},
            headers=admin_auth_headers,
        )

        # Duplicate add
        response = await client.post(
            f"/api/v1/diagnostics/centres/{centre_id}/tests",
            json={"test_id": test_id, "price": 600.00},
            headers=admin_auth_headers,
        )
        assert response.status_code == 409
