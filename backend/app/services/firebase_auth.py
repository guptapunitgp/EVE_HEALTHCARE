import firebase_admin
from firebase_admin import auth
from fastapi import HTTPException, status

from app.core import firebase  # noqa: F401 - initializes Firebase Admin when credentials are configured.
from app.core.config import settings


def verify_firebase_token(id_token: str) -> dict:
    try:
        if not firebase_admin._apps:
            raise RuntimeError("Firebase Admin SDK is not initialized")

        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        if settings.FIREBASE_PROJECT_ID and decoded_token.get("aud") != settings.FIREBASE_PROJECT_ID:
            raise ValueError("Firebase project mismatch")
        return decoded_token

    except Exception as error:
        import logging
        logging.getLogger(__name__).warning("Firebase token verification failed: %s", type(error).__name__)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase authentication token",
        )
