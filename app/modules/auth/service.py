"""
Auth Service
------------
Handles all authentication business logic including registration,
OTP verification, login, token refresh, and password management.

"""

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.infrastructure.celery.tasks import send_otp_email
from app.infrastructure.redis.client import (
    registration_cache,
    password_reset_cache,
    token_blacklist_cache,
    otp_cooldown_cache,
)
from app.modules.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.modules.users.repository import UserRepository
from app.shared.enums.role_enum import RoleEnum
from app.shared.responses.api_response import SuccessResponse
from app.shared.utils.constants import _MAX_OTP_ATTEMPTS
from app.shared.utils.otp_create import OTPService


class AuthService:

    # ──────────────────────────────────────────
    # Registration
    # ──────────────────────────────────────────

    @staticmethod
    async def send_registration_otp(data: RegisterRequest) -> SuccessResponse:
        """
        Step 1 of registration.
        Validates email is not taken, generates a 6-digit OTP,
        caches registration data, and dispatches email via Celery.
        Enforces 60-second cooldown between OTP sends.
        """
        if await UserRepository.email_exists(data.email):
            raise ConflictException("Email already registered")

        if await otp_cooldown_cache.get(data.email):
            raise ConflictException("Please wait 60 seconds before requesting a new OTP.")

        otp = OTPService.otp_generator(length=6)
        cache_data = data.model_dump()
        cache_data["otp"] = otp
        cache_data["attempts"] = 0

        await registration_cache.set(key=data.email, value=cache_data)
        await otp_cooldown_cache.set(key=data.email, value=True)
        send_otp_email.delay(data.email, otp)

        return SuccessResponse(message=f"OTP sent to {data.email}. Valid for 5 minutes.")







    @staticmethod
    async def verify_registration_otp(email: str, otp: str) -> RegisterResponse:
        """
        Step 2 of registration.
        Verifies OTP, creates user account, deletes cache, returns tokens.
        Locks out after 3 failed attempts to prevent brute force.
        """
        cached = await registration_cache.get(email)

        if cached is None:
            raise UnauthorizedException("OTP expired. Please register again.")

        # brute-force protection
        if cached.get("attempts", 0) >= _MAX_OTP_ATTEMPTS:
            await registration_cache.delete(email)
            raise UnauthorizedException("Too many failed attempts. Please register again.")

        if cached["otp"] != otp:
            cached["attempts"] += 1
            await registration_cache.set(key=email, value=cached)
            remaining = _MAX_OTP_ATTEMPTS - cached["attempts"]
            raise UnauthorizedException(f"Invalid OTP. {remaining} attempt(s) remaining.")

        await registration_cache.delete(email)

        user = await UserRepository.create(
            email=cached["email"],
            first_name=cached["first_name"],
            last_name=cached["last_name"],
            hashed_password=hash_password(cached["password"]),
            role=RoleEnum.CUSTOMER,
        )

        return RegisterResponse(
            uid=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            tokens=TokenResponse(
                access_token=create_access_token(str(user.id)),
                refresh_token=create_refresh_token(str(user.id)),
            ),
        )






    @staticmethod
    async def resend_registration_otp(email: str) -> SuccessResponse:
        """
        Resends a fresh OTP for an active registration session.
        Resets the attempt counter.
        Enforces 60-second cooldown between resends.
        """
        if await otp_cooldown_cache.get(email):
            raise ConflictException("Please wait 60 seconds before requesting a new OTP.")

        cached = await registration_cache.get(email)
        if cached is None:
            raise UnauthorizedException("Registration session expired. Please register again.")

        otp = OTPService.otp_generator(length=6)
        cached["otp"] = otp
        cached["attempts"] = 0
        await registration_cache.set(key=email, value=cached)
        await otp_cooldown_cache.set(key=email, value=True)
        send_otp_email.delay(email, otp)

        return SuccessResponse(message=f"OTP resent to {email}. Valid for 5 minutes.")

    # ──────────────────────────────────────────
    # Login & Token
    # ──────────────────────────────────────────

    @staticmethod
    async def login(data: LoginRequest) -> TokenResponse:
        """
        Authenticates user with email and password.
        Returns access + refresh token pair.
        """
        user = await UserRepository.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    @staticmethod
    async def refresh_token(refresh_token: str) -> AccessTokenResponse:
        """
        Issues a new access token from a valid refresh token.
        """
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            raise UnauthorizedException(str(e))

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        if await token_blacklist_cache.get(refresh_token):
            raise UnauthorizedException("Token has been revoked")

        user = await UserRepository.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or deactivated")

        return AccessTokenResponse(access_token=create_access_token(str(user.id)))

    @staticmethod
    async def logout(refresh_token: str) -> SuccessResponse:
        """
        Blacklists the refresh token so it cannot be reused.
        """
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            raise UnauthorizedException(str(e))

        # store until token natural expiry
        await token_blacklist_cache.set(key=refresh_token, value=True)
        return SuccessResponse(message="Logged out successfully.")

    # ──────────────────────────────────────────
    # Password Management
    # ──────────────────────────────────────────

    @staticmethod
    async def send_password_reset_otp(email: str) -> SuccessResponse:
        """
        Sends a password reset OTP.
        Does not reveal whether email exists (security best practice).
        Enforces 60-second cooldown between sends.
        """
        if await otp_cooldown_cache.get(email):
            raise ConflictException("Please wait 60 seconds before requesting a new OTP.")

        user = await UserRepository.get_by_email(email)
        if user:
            otp = OTPService.otp_generator(length=6)
            await password_reset_cache.set(key=email, value={"otp": otp, "attempts": 0})
            await otp_cooldown_cache.set(key=email, value=True)
            send_otp_email.delay(email, otp)

        return SuccessResponse(message="If this email exists, a reset OTP has been sent.")

    @staticmethod
    async def reset_password(email: str, otp: str, new_password: str) -> SuccessResponse:
        """
        Verifies OTP and updates the user password.
        Clears the reset cache and blacklists any active tokens on success.
        """
        cached = await password_reset_cache.get(email)
        if cached is None:
            raise UnauthorizedException("OTP expired. Please request a new one.")

        if cached.get("attempts", 0) >= _MAX_OTP_ATTEMPTS:
            await password_reset_cache.delete(email)
            raise UnauthorizedException("Too many failed attempts. Please request a new OTP.")

        if cached["otp"] != otp:
            cached["attempts"] += 1
            await password_reset_cache.set(key=email, value=cached)
            remaining = _MAX_OTP_ATTEMPTS - cached["attempts"]
            raise UnauthorizedException(f"Invalid OTP. {remaining} attempt(s) remaining.")

        user = await UserRepository.get_by_email(email)
        if not user:
            raise UnauthorizedException("User not found")

        await UserRepository.update(user, {"hashed_password": hash_password(new_password)})
        await password_reset_cache.delete(email)

        return SuccessResponse(message="Password changed successfully. Please log in again.")
