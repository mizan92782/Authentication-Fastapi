from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import ConflictException, UnauthorizedException
from app.modules.users.repository import UserRepository
from app.modules.auth.schemas import LoginRequest, TokenResponse, AccessTokenResponse
from app.modules.users.schemas import UserCreate, UserResponse


class AuthService:
    @staticmethod
    async def register(data: UserCreate) -> UserResponse:
        if await UserRepository.email_exists(data.email):
            raise ConflictException("Email already registered")
        if await UserRepository.username_exists(data.username):
            raise ConflictException("Username already taken")

        user = await UserRepository.create(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            phone=data.phone,
            address=data.address,
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
