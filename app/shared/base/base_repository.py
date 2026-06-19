from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)


class BaseRepository(Generic[ModelType]):
    model: Type[ModelType]

    @classmethod
    async def get_by_id(cls, id: Any) -> Optional[ModelType]:
        return await cls.model.get_or_none(id=id, is_deleted=False)

    @classmethod
    async def get_all(cls, **filters) -> List[ModelType]:
        return await cls.model.filter(is_deleted=False, **filters)

    @classmethod
    async def create(cls, **data) -> ModelType:
        return await cls.model.create(**data)

    @classmethod
    async def update(cls, instance: ModelType, data: Dict[str, Any]) -> ModelType:
        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)
        await instance.save()
        return instance

    @classmethod
    async def soft_delete(cls, instance: ModelType) -> None:
        await instance.soft_delete()

    @classmethod
    async def count(cls, **filters) -> int:
        return await cls.model.filter(is_deleted=False, **filters).count()
