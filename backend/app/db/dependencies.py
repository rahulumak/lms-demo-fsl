from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from app.db.session import get_db
from app.models.user import User, UserRole

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not credentials:
        raise exc
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(credentials.credentials)
        if payload.get("type") != "access":
            raise exc
        user_id: str = payload.get("sub")
    except jwt.PyJWTError:
        raise exc

    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise exc
    return user


def require_instructor(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.instructor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Instructor access required")
    return user


def require_student(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student access required")
    return user
