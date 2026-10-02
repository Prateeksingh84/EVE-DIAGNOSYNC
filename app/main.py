import os
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, close_db
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.routers import auth, diagnostics, bookings, payments, notifications, analytics
from app.services.cache_service import close_redis
from app.utils.exceptions import (
    global_exception_handler,
    http_exception_handler,
)


# ─── Structured Logging Configuration ─────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        structlog.get_config().get("min_level", 0)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# ─── Rate Limiter ─────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ─── App Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(
        "application_starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
    )
    await init_db()
    logger.info("database_initialized")

    # Auto-seed initial demo data if database is empty
    try:
        from app.seed import seed_data
        await seed_data()
    except Exception as e:
        logger.warning("auto_seed_skipped", error=str(e))

    yield
    await close_db()
    await close_redis()
    logger.info("application_shutdown")


# ─── FastAPI Application ──────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Backend service for diagnostic test bookings and simulated payments. "
        "Built for EVE Healthcare."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── State ────────────────────────────────────────────────────────────
app.state.limiter = limiter

# ─── Exception Handlers ──────────────────────────────────────────────
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Middleware ───────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure per environment in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────
app.include_router(
    auth.router, prefix=settings.API_V1_PREFIX
)
app.include_router(
    diagnostics.router, prefix=settings.API_V1_PREFIX
)
app.include_router(
    bookings.router, prefix=settings.API_V1_PREFIX
)
app.include_router(
    payments.router, prefix=settings.API_V1_PREFIX
)
app.include_router(
    notifications.router, prefix=settings.API_V1_PREFIX
)
app.include_router(
    analytics.router, prefix=settings.API_V1_PREFIX
)


# ─── Seed Demo Endpoint ───────────────────────────────────────────────
@app.post(
    f"{settings.API_V1_PREFIX}/seed",
    tags=["Seed"],
    summary="Seed demo diagnostic centres and tests",
)
async def seed_endpoint():
    """Populate initial demo data for diagnostic centres, tests, and demo users."""
    from app.seed import seed_data
    result = await seed_data()
    return result


# ─── Health Check ─────────────────────────────────────────────────────
@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    response_model=dict,
)
async def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ─── Interactive Web Dashboard ────────────────────────────────────────
DASHBOARD_PATH = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")


@app.get(
    "/",
    tags=["Dashboard"],
    response_class=HTMLResponse,
    summary="Interactive Web Dashboard UI",
)
@app.get(
    "/dashboard",
    tags=["Dashboard"],
    response_class=HTMLResponse,
    summary="Interactive Web Dashboard UI",
)
async def dashboard():
    """Serve the interactive real-time dashboard UI."""
    if os.path.exists(DASHBOARD_PATH):
        with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="""
        <html>
            <body style='font-family: sans-serif; text-align: center; padding: 50px;'>
                <h2>EVE Healthcare API</h2>
                <p>Visit <a href='/docs'>Swagger UI /docs</a> or <a href='/redoc'>ReDoc /redoc</a></p>
            </body>
        </html>
        """
    )


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint to prevent 404 logs."""
    from fastapi.responses import Response
    return Response(status_code=204)

