from celery import Celery
from celery.schedules import crontab
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)

celery_app = Celery(
    "eve_healthcare",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-pending-bookings": {
        "task": "app.tasks.celery_app.cleanup_expired_bookings",
        "schedule": crontab(minute="*/30"),
    },
}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def cleanup_expired_bookings(self):
    """
    Background task to clean up expired pending bookings.
    Bookings that have been PENDING for more than 30 minutes
    are automatically marked as FAILED.
    """
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import create_engine, update
    from sqlalchemy.orm import Session
    from app.models.booking import Booking, BookingStatus

    try:
        engine = create_engine(settings.DATABASE_URL_SYNC)
        with Session(engine) as session:
            threshold = datetime.now(timezone.utc) - timedelta(minutes=30)
            result = session.execute(
                update(Booking)
                .where(
                    Booking.status == BookingStatus.PENDING,
                    Booking.created_at < threshold,
                )
                .values(status=BookingStatus.FAILED)
            )
            session.commit()
            count = result.rowcount
            logger.info(
                "expired_bookings_cleaned",
                count=count,
            )
            return {"cleaned": count}
    except Exception as exc:
        logger.error(
            "cleanup_expired_bookings_failed", error=str(exc)
        )
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=30)
def process_webhook_async(self, webhook_payload: dict):
    """
    Background task to process webhook events with retry logic.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    try:
        logger.info(
            "processing_webhook_async",
            event_id=webhook_payload.get("event_id"),
        )
        # In a real system, this would process the webhook
        # Here we log it for demonstration
        return {
            "status": "processed",
            "event_id": webhook_payload.get("event_id"),
        }
    except Exception as exc:
        logger.error(
            "webhook_async_processing_failed",
            event_id=webhook_payload.get("event_id"),
            error=str(exc),
            retry_count=self.request.retries,
        )
        raise self.retry(exc=exc)
