from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.redis import redis_client

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
)-> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_access_token(credentials.credentials)
    if payload.get("jti"):
        try:
            if await redis_client.get(f"revoked-token:{payload['jti']}"):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been signed out")
        except HTTPException:
            raise
        except Exception as error:
            raise HTTPException(status_code=503, detail="Session validation is temporarily unavailable") from error
    user_id: UUID = payload["user_id"]

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account is disabled",
        )

    return user
