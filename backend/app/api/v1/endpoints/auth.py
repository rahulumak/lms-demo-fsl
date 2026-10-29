from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(request: Request, data: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    return auth_service.register_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(request: Request, data: LoginRequest, response: Response, db: Annotated[Session, Depends(get_db)]):
    token = auth_service.login_user(db, data, response)
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, db: Annotated[Session, Depends(get_db)]):
    token = auth_service.refresh_session(db, request, response)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Annotated[Session, Depends(get_db)]):
    auth_service.logout_user(db, request, response)


@router.get("/me", response_model=UserOut)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
