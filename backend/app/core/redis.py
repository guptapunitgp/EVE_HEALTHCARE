import redis.asyncio as redis
import ssl
import socket
from urllib.parse import urlsplit
from redis.exceptions import AuthenticationError, TimeoutError as RedisTimeoutError

from app.core.config import settings


redis_options = {
    "decode_responses": False,
    "socket_connect_timeout": 3,
    "socket_timeout": 3,
    "health_check_interval": 30,
}
if urlsplit(settings.REDIS_URL).scheme == "rediss":
    redis_options["ssl_cert_reqs"] = ssl.CERT_REQUIRED

redis_client = redis.Redis.from_url(settings.REDIS_URL, **redis_options)


def redis_failure_category(error: Exception) -> str:
    """Return a safe diagnostic label without logging connection details."""
    current: BaseException | None = error
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
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
    return "connection"


def get_redis():
    return redis_client
