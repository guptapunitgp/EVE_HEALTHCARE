from celery import Celery
import ssl
from urllib.parse import urlsplit

from app.core.config import settings

celery_app = Celery(
    "eve_healthcare",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.services.notification_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
)

# Upstash and other managed Redis providers expose TLS endpoints with rediss://.
# Celery's redis transport requires explicit certificate verification options.
if urlsplit(settings.CELERY_BROKER_URL).scheme == "rediss":
    celery_app.conf.broker_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
if urlsplit(settings.CELERY_RESULT_BACKEND).scheme == "rediss":
    celery_app.conf.redis_backend_use_ssl = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
