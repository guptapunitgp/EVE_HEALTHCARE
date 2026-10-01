from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.centre_tests import router as centre_tests_router
from app.api.routes.centres import router as centres_router
from app.api.routes.health import router as health_router
from app.api.routes.payments import router as payments_router
from app.api.routes.tests import router as tests_router
from app.api.routes.admin import router as admin_router
from app.api.routes.staff import router as staff_router
from app.api.routes.ai import router as ai_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(centres_router)
api_router.include_router(tests_router)
api_router.include_router(centre_tests_router)
api_router.include_router(bookings_router)
api_router.include_router(payments_router)
api_router.include_router(admin_router)
api_router.include_router(staff_router)
api_router.include_router(ai_router)
