import pytest
from pydantic import ValidationError
import socket

from app.core.config import Settings
from app.core.redis import redis_failure_category


def test_upstash_tls_url_is_accepted_and_used_by_celery():
    url = "rediss://default:secret@example.upstash.io:6379"
    settings = Settings(_env_file=None, REDIS_URL=url)

    assert settings.REDIS_URL == url
    assert settings.CELERY_BROKER_URL == url
    assert settings.CELERY_RESULT_BACKEND == url


def test_upstash_cli_redis_url_is_normalized_to_tls():
    settings = Settings(
        _env_file=None,
        REDIS_URL="redis://default:placeholder@example.upstash.io:6379",
    )

    assert settings.REDIS_URL.startswith("rediss://")
    assert settings.CELERY_BROKER_URL == settings.REDIS_URL
    assert settings.CELERY_RESULT_BACKEND == settings.REDIS_URL


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (socket.gaierror("private-hostname"), "dns_resolution"),
        (TimeoutError("private detail"), "timeout"),
        (ConnectionRefusedError("private detail"), "connection_refused"),
    ],
)
def test_redis_failure_category_does_not_emit_error_details(error, expected):
    assert redis_failure_category(error) == expected


def test_invalid_redis_url_has_safe_error():
    secret_url = "https://default:do-not-log@example.upstash.io:6379"

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, REDIS_URL=secret_url)

    assert "do-not-log" not in str(error.value)
    assert "redis:// or rediss://" in str(error.value)


def test_production_rejects_local_redis_defaults():
    with pytest.raises(ValidationError, match="Production Redis and Celery URLs"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+psycopg://eve:password@db.example.test/eve",
            JWT_SECRET_KEY="a-strong-test-secret-with-more-than-32-characters",
            CORS_ORIGINS="https://example.test",
        )
