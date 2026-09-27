from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.user import User
from app.schemas.user import UserCreate
from app.security import hash_password, verify_password
from app.utils.exceptions import ConflictException, BadRequestException

logger = structlog.get_logger(__name__)


async def get_user_by_email(
    db: AsyncSession, email: str
) -> Optional[User]:
    """Retrieve a user by their email address."""
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[User]:
    """Retrieve a user by their ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user account."""
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        raise ConflictException(
            detail="A user with this email already exists"
        )

    user = User(
        email=user_data.email.lower(),
        full_name=user_data.full_name,
        phone=user_data.phone,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    logger.info("user_created", user_id=str(user.id), email=user.email)
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> User:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email)
    if not user:
        raise BadRequestException(detail="Invalid email or password")

    if not verify_password(password, user.hashed_password):
        logger.warning(
            "failed_login_attempt", email=email
        )
        raise BadRequestException(detail="Invalid email or password")

    if not user.is_active:
        raise BadRequestException(detail="User account is deactivated")

    logger.info("user_authenticated", user_id=str(user.id))
    return user
