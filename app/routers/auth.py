from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefreshRequest,
    LogoutRequest,
)
from app.security import create_access_token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
async def signup(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await auth_service.create_user(db, user_data)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get tokens",
    description="Authenticate with email and password to receive JWT access and rotating refresh tokens.",
)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user = await auth_service.authenticate_user(
        db, credentials.email, credentials.password
    )

    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={"email": user.email, "is_admin": user.is_admin},
    )
    # Issue stateful, rotating refresh token with family tracking
    refresh_token = await auth_service.issue_refresh_token(db, user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token",
    description="Exchange a valid refresh token for a new access token and a new rotated refresh token. Detects replay attacks.",
)
async def refresh_tokens(
    refresh_req: TokenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    new_access, new_refresh, expires_in = await auth_service.rotate_refresh_token(
        db, refresh_req.refresh_token
    )
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=expires_in,
    )


@router.post(
    "/logout",
    summary="Revoke tokens / Logout",
    description="Invalidate the active refresh token to securely terminate the session.",
)
async def logout(
    logout_req: LogoutRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if logout_req.refresh_token:
        await auth_service.revoke_refresh_token(db, logout_req.refresh_token)
    return {"status": "success", "message": "Successfully logged out and session revoked."}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information.",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user
