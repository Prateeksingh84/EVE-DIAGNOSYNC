import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
class TestSignup:
    """Tests for the user signup endpoint."""

    async def test_signup_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "StrongPass123!",
                "full_name": "New User",
                "phone": "+1234567890",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data

    async def test_signup_duplicate_email(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": test_user.email,
                "password": "StrongPass123!",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 409

    async def test_signup_weak_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "full_name": "Weak User",
            },
        )
        assert response.status_code == 422

    async def test_signup_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={
                "email": "not-an-email",
                "password": "StrongPass123!",
                "full_name": "Bad Email User",
            },
        )
        assert response.status_code == 422

    async def test_signup_missing_fields(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"email": "partial@example.com"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    """Tests for the user login endpoint."""

    async def test_login_success(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "TestPass123!",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_wrong_password(
        self, client: AsyncClient, test_user: User
    ):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "WrongPass123!",
            },
        )
        assert response.status_code == 400

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "noone@example.com",
                "password": "SomePass123!",
            },
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestMe:
    """Tests for the get current user endpoint."""

    async def test_get_me_authenticated(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        response = await client.get(
            "/api/v1/auth/me", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403  # No auth header

    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
