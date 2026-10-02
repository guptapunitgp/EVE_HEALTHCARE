from fastapi import APIRouter

from app.core.redis import redis_client, redis_failure_category
from app.db.database import engine
from sqlalchemy import text

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    redis_status = False
    redis_error_category = None

    try:
        redis_status = await redis_client.ping()
    except Exception as error:
        redis_status = False
        redis_error_category = redis_failure_category(error)

    return {
        "success": True,
        "status": "healthy" if redis_status else "degraded",
        "message": "EVE Healthcare API is responding",
        "redis": redis_status,
        "redis_error_category": redis_error_category,
    }


@router.get("/ready")
async def readiness_check():
    checks = {"database": False, "redis": False}
    diagnostics = {}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        checks["redis"] = bool(await redis_client.ping())
    except Exception as error:
        diagnostics["redis"] = redis_failure_category(error)
    from fastapi import HTTPException

    if not all(checks.values()):
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks,
                "diagnostics": diagnostics,
            },
        )
    return {"status": "ready", "checks": checks}
