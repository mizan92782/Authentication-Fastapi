import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
import re


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("Username must be 3-30 alphanumeric characters or underscores")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool


class UserInDB(UserResponse):
    hashed_password: str
