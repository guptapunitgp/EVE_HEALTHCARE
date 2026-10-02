import redis.asyncio as redis
import ssl
import socket
from urllib.parse import urlsplit
from redis.exceptions import (
    AuthenticationError,
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)

from app.core.config import settings


redis_options = {
    "decode_responses": False,
    "socket_connect_timeout": 5,
    "socket_timeout": 5,
    "health_check_interval": 30,
}
if urlsplit(settings.REDIS_URL).scheme == "rediss":
    redis_options["ssl_cert_reqs"] = ssl.CERT_REQUIRED

redis_client = redis.Redis.from_url(settings.REDIS_URL, **redis_options)


def redis_failure_category(error: Exception) -> str:
    """Return a safe diagnostic label without logging connection details."""
    current: BaseException | None = error
    seen: set[int] = set()
    messages: list[str] = []
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        messages.extend(arg.lower() for arg in current.args if isinstance(arg, str))
        if isinstance(current, AuthenticationError):
            return "authentication"
        if isinstance(current, ssl.SSLError):
            return "tls_handshake"
        if isinstance(current, socket.gaierror):
            return "dns_resolution"
        if isinstance(current, (TimeoutError, RedisTimeoutError, socket.timeout)):
            return "timeout"
        if isinstance(current, ConnectionRefusedError):
            return "connection_refused"
        current = current.__cause__ or current.__context__

    # redis-py wraps socket OSErrors as ConnectionError strings, so inspect
    # the message only to classify it; never return or log the message itself.
    detail = " ".join(messages)
    if any(
        marker in detail
        for marker in (
            "noauth",
            "authentication required",
            "invalid username-password",
            "wrongpass",
        )
    ):
        return "authentication"
    if any(
        marker in detail
        for marker in (
            "getaddrinfo failed",
            "name or service not known",
            "no such host",
            "name resolution",
        )
    ):
        return "dns_resolution"
    if any(marker in detail for marker in ("connection refused", "actively refused")):
        return "connection_refused"
    if any(marker in detail for marker in ("timed out", "timeout")):
        return "timeout"
    if any(
        marker in detail
        for marker in ("certificate", "ssl", "tls", "wrong version number")
    ):
        return "tls_handshake"
    if any(
        marker in detail
        for marker in ("network is unreachable", "no route to host", "connection reset")
    ):
        return "network"
    if isinstance(error, RedisConnectionError):
        return "connection"
    return "connection"


def get_redis():
    return redis_client
