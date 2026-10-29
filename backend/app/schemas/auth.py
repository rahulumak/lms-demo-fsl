from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full_name is required")
        if len(v) > 200:
            raise ValueError("full_name must be 200 characters or fewer")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password must be 128 characters or fewer")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
