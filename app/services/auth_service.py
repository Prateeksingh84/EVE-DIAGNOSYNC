import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.user import UserCreate
from app.security import hash_password, verify_password, create_access_token
from app.utils.exceptions import ConflictException, BadRequestException, UnauthorizedException

logger = structlog.get_logger(__name__)


def _hash_token(token: str) -> str:
    """Hash a token with SHA-256 for secure DB storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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


async def issue_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    family_id: Optional[uuid.UUID] = None,
) -> str:
    """
    Issue and store a cryptographically secure refresh token.
    Uses token families to detect and neutralize replay attacks.
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)
    fam_id = family_id or uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    db_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        family_id=fam_id,
        is_revoked=False,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.flush()
    return raw_token


async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> Tuple[str, str, int]:
    """
    Rotate a refresh token.
    - If valid: revokes the old token, issues a new access token and new refresh token.
    - If already revoked (replay attack): revokes all tokens in the family for security!
    """
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise UnauthorizedException(detail="Invalid refresh token")

    # Replay attack detection: token was already revoked/used!
    if db_token.is_revoked:
        logger.critical(
            "refresh_token_reuse_detected",
            family_id=str(db_token.family_id),
            user_id=str(db_token.user_id),
        )
        # Invalidate the entire token family
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == db_token.family_id)
            .values(is_revoked=True)
        )
        await db.flush()
        raise UnauthorizedException(
            detail="Security alert: Refresh token reuse detected. All sessions revoked."
        )

    # Check expiration
    exp = db_token.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        db_token.is_revoked = True
        await db.flush()
        raise UnauthorizedException(detail="Refresh token has expired")

    # Mark current token as revoked / rotated
    db_token.is_revoked = True

    # Retrieve user to embed claims
    user = await get_user_by_id(db, db_token.user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(detail="User account is inactive or not found")

    # Issue new refresh token within the SAME family
    new_refresh_token = await issue_refresh_token(
        db, user.id, family_id=db_token.family_id
    )

    # Issue new access token
    new_access_token = create_access_token(
        subject=str(user.id),
        additional_claims={"email": user.email, "is_admin": user.is_admin},
    )

    await db.flush()

    logger.info("refresh_token_rotated", user_id=str(user.id), family_id=str(db_token.family_id))
    return new_access_token, new_refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> bool:
    """Revoke a refresh token on user logout."""
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True
        await db.flush()
        logger.info("refresh_token_revoked", token_id=str(db_token.id))
        return True
    return False
