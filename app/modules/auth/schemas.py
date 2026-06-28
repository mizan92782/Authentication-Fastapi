"""
Auth Schemas
------------
Pydantic models for request validation and response serialization
across the authentication flow.
"""

import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ──────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """User registration request. OTP will be sent to the provided email."""

    first_name: str = Field(..., min_length=1, max_length=30, examples=["John"])
    last_name: str = Field(..., min_length=1, max_length=30, examples=["Doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=8, max_length=32, examples=["Secret@123"])
    confirm_password: str = Field(..., min_length=8, max_length=32, examples=["Secret@123"])

    @model_validator(mode="after")
    def passwords_must_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class OtpVerifyRequest(BaseModel):
    """OTP verification for completing registration."""

    email: EmailStr = Field(..., examples=["john@example.com"])
    otp: str = Field(..., min_length=6, max_length=6, examples=["123456"])


class OtpResendRequest(BaseModel):
    """Resend OTP to the provided email."""

    email: EmailStr = Field(..., examples=["john@example.com"])


# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Login with email and password."""

    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., examples=["Secret@123"])


# ──────────────────────────────────────────────
# Password Reset
# ──────────────────────────────────────────────

class PasswordResetRequest(BaseModel):
    """Request a password reset OTP."""

    email: EmailStr = Field(..., examples=["john@example.com"])


class PasswordChangeRequest(BaseModel):
    """Change password using the OTP received via email."""

    email: EmailStr = Field(..., examples=["john@example.com"])
    otp: str = Field(..., min_length=6, max_length=6, examples=["123456"])
    new_password: str = Field(..., min_length=8, max_length=32, examples=["NewSecret@123"])
    confirm_password: str = Field(..., min_length=8, max_length=32, examples=["NewSecret@123"])

    @model_validator(mode="after")
    def passwords_must_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# ──────────────────────────────────────────────
# Responses
# ──────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT token pair returned on successful login or registration."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """New access token returned on refresh."""

    access_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """Returned after successful OTP verification and user creation."""

    uid: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    tokens: TokenResponse
