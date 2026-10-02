from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.api.router import api_router
from app.core.redis import redis_client, redis_failure_category
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("eve.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))[:128]
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_id=%s method=%s path=%s status=%s duration_ms=%.2f", request_id, request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(
        RedisBackend(redis_client),
        prefix="eve-healthcare-cache",
    )
    try:
        try:
            await redis_client.ping()
        except Exception as error:
            logger.warning("redis_startup_check_failed category=%s", redis_failure_category(error))
        yield
    finally:
        await redis_client.aclose()


app = FastAPI(
    title="EVE Healthcare API",
    description="Diagnostic test booking and simulated payment API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "success": True,
        "message": "EVE Healthcare API is running",
    }
