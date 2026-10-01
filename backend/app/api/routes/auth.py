from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.user import (
    FirebaseLoginRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.services.firebase_auth import verify_firebase_token
from app.core.config import settings
from fastapi import HTTPException
from app.core.redis import redis_client
from app.api.dependencies import security


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/dev-login")
def dev_login(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    if not settings.ENABLE_DEV_AUTH or settings.ENVIRONMENT != "development":
        raise HTTPException(status_code=404, detail="Not found")
    user = db.query(User).filter(User.email == user_data.email).first()

    if user is None:
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled")

    access_token = create_access_token(user.id)

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/firebase")
def firebase_login(
    login_data: FirebaseLoginRequest,
    db: Session = Depends(get_db),
):
    firebase_user = verify_firebase_token(login_data.id_token)

    firebase_uid = firebase_user["uid"]
    email = firebase_user.get("email")

    if not email or not firebase_user.get("email_verified", False):
        raise HTTPException(status_code=401, detail="A verified email is required")

    full_name = firebase_user.get("name")

    user = (
        db.query(User)
        .filter(User.firebase_uid == firebase_uid)
        .first()
    )

    if user is None:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            firebase_uid=firebase_uid,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    elif user.firebase_uid != firebase_uid:
        if user.firebase_uid:
            raise HTTPException(status_code=409, detail="Account is linked to another identity")
        user.firebase_uid = firebase_uid

        if full_name and not user.full_name:
            user.full_name = full_name

        db.commit()
        db.refresh(user)

    if settings.INITIAL_ADMIN_EMAIL and email.casefold() == settings.INITIAL_ADMIN_EMAIL.casefold():
        user.role = "admin"
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled")

    access_token = create_access_token(user.id)

    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.get("/me", response_model=UserResponse)
def current_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_profile(data: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if "full_name" in data.model_fields_set:
        current_user.full_name = data.full_name.strip() if data.full_name else None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/logout", status_code=204)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
):
    try:
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        remaining = max(1, int(payload["exp"] - datetime.now(timezone.utc).timestamp()))
        if payload.get("jti"):
            await redis_client.setex(f"revoked-token:{payload['jti']}", remaining, "1")
    except Exception as error:
        raise HTTPException(status_code=503, detail="Could not invalidate this session") from error
    return None
