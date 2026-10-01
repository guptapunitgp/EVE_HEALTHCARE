from fastapi import APIRouter

from app.core.redis import redis_client
from app.db.database import engine
from sqlalchemy import text

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    redis_status = False

    try:
        redis_status = await redis_client.ping()
    except Exception:
        redis_status = False

    return {
        "success": True,
        "message": "EVE Healthcare API is healthy",
        "redis": redis_status,
    }


@router.get("/ready")
async def readiness_check():
    checks = {"database": False, "redis": False}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        checks["redis"] = bool(await redis_client.ping())
    except Exception:
        pass
    from fastapi import HTTPException
    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}
