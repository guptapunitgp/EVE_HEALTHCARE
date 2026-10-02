import redis.asyncio as redis
import ssl
from urllib.parse import urlsplit

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


def get_redis():
    return redis_client
