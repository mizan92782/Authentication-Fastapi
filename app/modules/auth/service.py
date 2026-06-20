from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import ConflictException, UnauthorizedException, BadRequestException
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse, AccessTokenResponse, OtpVeritySchema, OtpVeritySchemaResponse
from app.modules.users.schemas import UserCreate, UserResponse
from app.shared.enums.role_enum import RoleEnum
from app.infrastructure.redis.client import registration_cache
from app.infrastructure.celery.tasks import registraion_otp_send_eamil_delay
from app.shared.responses.api_response import SuccessResponse, ErrorResponse
from app.shared.utils.opt import OTPService


class AuthService:
    
    @staticmethod
    async def registration_otp_cache(data):
        if await UserRepository.email_exists(data.email):
            raise ConflictException("Email alredy registered")

        #=== generte opt and add opt to data field
        otp = OTPService.otp_generator(4)
        #=====set data in cache
        cached = data.model_dump()
        cached["otp"] = otp
        key=registration_cache._key(data.email)
        await registration_cache.set(key, value=cached)
        registraion_otp_send_eamil_delay.delay(data.email, otp)

        return SuccessResponse(message=f"OTP sent to {data.email}. Verify within 5 minutes.")
    
    @staticmethod
    async def registration_otp_verification(data: OtpVeritySchema):
        key = registration_cache._key(data.email)
        
        
        
        cached = await registration_cache.get(key)
        if not cached:
            raise BadRequestException("OTP expired or not found. Please register again.")
        if cached["otp"] != data.otp:
            raise BadRequestException("Invalid OTP.")
        user = await User.create(
            email=cached["email"],
            first_name=cached["first_name"],
            last_name=cached["last_name"],
            hashed_password=hash_password(cached["password1"]),
            role=RoleEnum.CUSTOMER,
        )
        await registration_cache.delete(key)
        return OtpVeritySchemaResponse(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            dp=user.dp,
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )
        


    @staticmethod
    async def register(data: UserCreate) -> UserResponse:
        if await UserRepository.email_exists(data.email):
            raise ConflictException("Email already registered")
        if await UserRepository.username_exists(data.username):
            raise ConflictException("Username already taken")

        user = await UserRepository.create(
            email=data.email,
            first_name = data.firs_name,
            last_name=data.last_name,
            hashed_password=hash_password(data.password),
            role = RoleEnum.ADMIN
            
            
        )
        return UserResponse.model_validate(user)

    @staticmethod
    async def login(data: LoginRequest) -> TokenResponse:
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
    async def refresh(refresh_token: str) -> AccessTokenResponse:
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            raise UnauthorizedException(str(e))

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        user = await UserRepository.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or deactivated")

        return AccessTokenResponse(access_token=create_access_token(str(user.id)))
