"""
Auth Routes
-----------
All authentication endpoints grouped under /auth prefix.

"""

from fastapi import APIRouter, Form, Request
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    AccessTokenResponse,
    OtpResendRequest,
)
from app.shared.responses.api_response import SuccessResponse
from app.core.limiter import limiter

auth_router = APIRouter()


# ──────────────────────────────────────────────
# Registration Flow
# ──────────────────────────────────────────────

@auth_router.post(
    "/user/register/",
    response_model=SuccessResponse,
    summary="Step 1 — Register and receive OTP",
    description="Validates user data and sends a 6-digit OTP to the provided email. OTP expires in 5 minutes.",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    first_name: str = Form(..., description="First name", examples=["John"]),
    last_name: str = Form(..., description="Last name", examples=["Doe"]),
    email: str = Form(..., description="Valid email address", examples=["john@example.com"]),
    password: str = Form(..., description="Min 8 characters", examples=["Secret@123"]),
    confirm_password: str = Form(..., description="Must match password", examples=["Secret@123"]),
):
    data = RegisterRequest(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        confirm_password=confirm_password,
    )
    return await AuthService.send_registration_otp(data)


@auth_router.post(
    "/user/otp-verify/",
    response_model=RegisterResponse,
    summary="Step 2 — Verify OTP and complete registration",
    description="Verifies the OTP. On success, creates the user account and returns access + refresh tokens.",
)
@limiter.limit("10/minute")
async def otp_verify(
    request: Request,
    email: str = Form(..., description="Registered email", examples=["john@example.com"]),
    otp: str = Form(..., description="6-digit OTP from email", examples=["123456"]),
):
    return await AuthService.verify_registration_otp(email, otp)


@auth_router.post(
    "/user/otp-resend/",
    response_model=SuccessResponse,
    summary="Resend registration OTP",
    description="Resends a fresh OTP. Only works if the registration session is still active.",
)
@limiter.limit("3/minute")
async def otp_resend(
    request: Request,
    email: str = Form(..., description="Registered email", examples=["john@example.com"]),
):
    return await AuthService.resend_registration_otp(email)


# ──────────────────────────────────────────────
# Login & Token
# ──────────────────────────────────────────────

@auth_router.post(
    "/user/login/",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password. Returns access and refresh tokens.",
)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest):
    return await AuthService.login(data)


@auth_router.post(
    "/user/token-refresh/",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Provide a valid refresh token to receive a new access token.",
)
async def token_refresh(
    refresh_token: str = Form(..., description="Valid refresh token"),
):
    return await AuthService.refresh_token(refresh_token)


@auth_router.post(
    "/user/logout/",
    response_model=SuccessResponse,
    summary="Logout",
    description="Blacklists the refresh token. The token cannot be used again after logout.",
)
async def logout(
    refresh_token: str = Form(..., description="Refresh token to invalidate"),
):
    return await AuthService.logout(refresh_token)


# ──────────────────────────────────────────────
# Password Management
# ──────────────────────────────────────────────

@auth_router.post(
    "/user/password-reset/",
    response_model=SuccessResponse,
    summary="Request password reset OTP",
    description="Sends a 6-digit OTP to the email if it exists. Always returns the same message to prevent email enumeration.",
)
@limiter.limit("5/minute")
async def password_reset(
    request: Request,
    email: str = Form(..., description="Registered email", examples=["john@example.com"]),
):
    return await AuthService.send_password_reset_otp(email)


@auth_router.post(
    "/user/password-change/",
    response_model=SuccessResponse,
    summary="Change password using OTP",
    description="Verifies OTP and updates the password. Locked out after 3 failed attempts.",
)
@limiter.limit("5/minute")
async def password_change(
    request: Request,
    email: str = Form(..., description="Registered email", examples=["john@example.com"]),
    otp: str = Form(..., description="6-digit OTP from email", examples=["123456"]),
    new_password: str = Form(..., description="New password min 8 characters", examples=["NewSecret@123"]),
    confirm_password: str = Form(..., description="Must match new password", examples=["NewSecret@123"]),
):
    data = PasswordChangeRequest(
        email=email,
        otp=otp,
        new_password=new_password,
        confirm_password=confirm_password,
    )
    return await AuthService.reset_password(data.email, data.otp, data.new_password)
