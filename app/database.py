from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)


def _create_engine_instance(url: str):
    kwargs = {"echo": settings.DEBUG}
    if not url.startswith("sqlite"):
        kwargs.update({
            "pool_size": 20,
            "max_overflow": 10,
            "pool_pre_ping": True,
        })
    return create_async_engine(url, **kwargs)


engine = _create_engine_instance(settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db():
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables. If PostgreSQL is unreachable, automatically fall back to local SQLite."""
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        db_identifier = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
        logger.info("database_tables_initialized", target=db_identifier)
    except Exception as e:
        if not settings.DATABASE_URL.startswith("sqlite"):
            fallback_url = "sqlite+aiosqlite:///./eve_healthcare.db"
            logger.warning(
                "postgres_connection_failed",
                error=str(e),
                fallback="sqlite",
                message=f"PostgreSQL not reachable at {settings.DATABASE_URL}. Automatically falling back to local SQLite ({fallback_url}) for development.",
            )
            await engine.dispose()
            engine = _create_engine_instance(fallback_url)
            AsyncSessionLocal.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("sqlite_fallback_initialized", database="./eve_healthcare.db")
        else:
            raise


async def close_db():
    """Dispose the engine connection pool."""
    await engine.dispose()
