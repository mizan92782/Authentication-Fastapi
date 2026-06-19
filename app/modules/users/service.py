from app.core.exceptions import NotFoundException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate


class UserService:
    @staticmethod
    async def get_by_id(user_id: str) -> UserResponse:
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        return UserResponse.model_validate(user)

    @staticmethod
    async def update(user_id: str, data: UserUpdate) -> UserResponse:
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        updated = await UserRepository.update(user, data.model_dump(exclude_none=True))
        return UserResponse.model_validate(updated)

    @staticmethod
    async def delete(user_id: str) -> None:
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        await UserRepository.soft_delete(user)
