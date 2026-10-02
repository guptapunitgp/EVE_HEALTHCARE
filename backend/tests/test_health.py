import asyncio
from contextlib import nullcontext

from fastapi import HTTPException

from redis.exceptions import ConnectionError as RedisConnectionError

from app.api.routes import health


class FailingRedis:
    async def ping(self):
        raise RedisConnectionError("TLSV1_ALERT_INTERNAL_ERROR")


class FakeConnection:
    def execute(self, _query):
        return 1


def test_health_reports_safe_redis_failure_category(monkeypatch):
    monkeypatch.setattr(health, "redis_client", FailingRedis())

    result = asyncio.run(health.health_check())

    assert result["redis"] is False
    assert result["redis_error_category"] == "tls_peer_alert"


def test_readiness_reports_safe_redis_failure_category(monkeypatch):
    monkeypatch.setattr(health, "redis_client", FailingRedis())
    monkeypatch.setattr(
        health,
        "engine",
        type(
            "FakeEngine", (), {"connect": lambda self: nullcontext(FakeConnection())}
        )(),
    )

    try:
        asyncio.run(health.readiness_check())
    except HTTPException as error:
        assert error.status_code == 503
        assert error.detail["checks"] == {"database": True, "redis": False}
        assert error.detail["diagnostics"]["redis"] == "tls_peer_alert"
    else:
        raise AssertionError("Readiness must fail while Redis is unavailable")
