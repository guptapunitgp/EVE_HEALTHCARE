import firebase_admin
from firebase_admin import credentials

from app.core.config import settings


if not firebase_admin._apps and settings.FIREBASE_CREDENTIALS_PATH:
    credential = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

    firebase_admin.initialize_app(credential, {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None)
