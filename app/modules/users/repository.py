from typing import Optional
from app.modules.users.models import User
from app.shared.base.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    @classmethod
    async def get_by_email(cls, email: str) -> Optional[User]:
        return await User.get_or_none(email=email, is_deleted=False)

    @classmethod
    async def get_by_username(cls, username: str) -> Optional[User]:
        return await User.get_or_none(username=username, is_deleted=False)

    @classmethod
    async def email_exists(cls, email: str) -> bool:
        return await User.filter(email=email).exists()

    @classmethod
    async def username_exists(cls, username: str) -> bool:
        return await User.filter(username=username).exists()
