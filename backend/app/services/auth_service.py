from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, generate_refresh_token, hash_refresh_token,
)
from app.models.user import User, UserRole
from app.models.auth_session import AuthSession
from app.schemas.auth import RegisterRequest, LoginRequest

COOKIE_NAME = "refresh_token"


def _verify_origin(request: Request) -> None:
    """CSRF guard: reject requests whose Origin/Referer is not in ALLOWED_ORIGINS."""
    allowed = set(settings.allowed_origins_list)
    origin = request.headers.get("origin") or request.headers.get("referer", "")
    # Strip trailing path from Referer so we compare just the origin
    from urllib.parse import urlparse
    parsed = urlparse(origin)
    request_origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
    if request_origin not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF check failed",
        )


def register_user(db: Session, data: RegisterRequest) -> User:
    email = data.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registration failed")
    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        role=UserRole.student,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, data: LoginRequest, response: Response) -> str:
    email = data.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    raw_token = generate_refresh_token()
    session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session)
    db.commit()

    _set_refresh_cookie(response, raw_token)
    return create_access_token(str(user.id), user.role.value)


def refresh_session(db: Session, request: Request, response: Response) -> str:
    _verify_origin(request)
    raw_token = request.cookies.get(COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    token_hash = hash_refresh_token(raw_token)
    now = datetime.now(timezone.utc)
    session = db.query(AuthSession).filter(
        AuthSession.refresh_token_hash == token_hash,
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > now,
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    # Rotate refresh token
    session.revoked_at = now
    new_raw = generate_refresh_token()
    new_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(new_raw),
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        last_used_at=now,
    )
    db.add(new_session)
    db.commit()

    _set_refresh_cookie(response, new_raw)
    return create_access_token(str(user.id), user.role.value)


def logout_user(db: Session, request: Request, response: Response) -> None:
    _verify_origin(request)
    raw_token = request.cookies.get(COOKIE_NAME)
    if raw_token:
        token_hash = hash_refresh_token(raw_token)
        session = db.query(AuthSession).filter(AuthSession.refresh_token_hash == token_hash).first()
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
    response.delete_cookie(COOKIE_NAME)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )
