import json

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings


if not firebase_admin._apps and settings.FIREBASE_CREDENTIALS_PATH:
    credential = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)

    firebase_admin.initialize_app(credential, {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None)
elif not firebase_admin._apps and settings.FIREBASE_CREDENTIALS_JSON:
    credentials_json = settings.FIREBASE_CREDENTIALS_JSON.get_secret_value()
    if credentials_json.strip():
        service_account = json.loads(credentials_json)
    else:
        service_account = None
    if service_account:
        credential = credentials.Certificate(service_account)
        firebase_admin.initialize_app(credential, {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None)
