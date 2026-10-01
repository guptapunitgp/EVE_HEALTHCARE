import logging
from datetime import datetime
from sqlalchemy import select
from app.db.database import SessionLocal
from app.models.notification_outbox import NotificationOutbox

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="notifications.send_mock_notification")
def send_mock_notification(
    notification_type: str,
    booking_id: str,
    status: str,
):
    message = (
        f"[MOCK NOTIFICATION] Type: {notification_type} | "
        f"Booking ID: {booking_id} | Status: {status}"
    )

    logger.info(message)

    return {
        "success": True,
        "mock": True,
        "message": message,
    }


@celery_app.task(name="notifications.dispatch_outbox")
def dispatch_outbox():
    """Drain durable notification records; failed deliveries remain retryable."""
    delivered = 0
    with SessionLocal() as db:
        pending = db.scalars(
            select(NotificationOutbox)
            .where(NotificationOutbox.status == "pending")
            .order_by(NotificationOutbox.created_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        ).all()
        for event in pending:
            try:
                logger.info("mock_notification event_id=%s type=%s payload=%s", event.id, event.event_type, event.payload)
                event.status = "sent"
                event.attempts += 1
                event.processed_at = datetime.utcnow()
                event.last_error = None
                delivered += 1
            except Exception as error:
                event.status = "pending"
                event.attempts += 1
                event.last_error = type(error).__name__
        db.commit()
    return {"delivered": delivered}


celery_app.conf.beat_schedule = {
    "dispatch-notification-outbox": {
        "task": "notifications.dispatch_outbox",
        "schedule": 30.0,
    },
}
