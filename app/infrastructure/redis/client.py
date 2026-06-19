import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


class CacheClient:
    def __init__(self, prefix: str = "", ttl: int = settings.redis_ttl):
        self.prefix = prefix
        self.ttl = ttl

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}" if self.prefix else key

    async def get(self, key: str) -> Optional[Any]:
        try:
            redis = await get_redis()
            value = await redis.get(self._key(key))
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning("cache_get_error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        try:
            redis = await get_redis()
            await redis.setex(self._key(key), ttl or self.ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning("cache_set_error", key=key, error=str(e))

    async def delete(self, key: str) -> None:
        try:
            redis = await get_redis()
            await redis.delete(self._key(key))
        except Exception as e:
            logger.warning("cache_delete_error", key=key, error=str(e))

    async def delete_pattern(self, pattern: str) -> None:
        try:
            redis = await get_redis()
            keys = await redis.keys(self._key(pattern))
            if keys:
                await redis.delete(*keys)
        except Exception as e:
            logger.warning("cache_delete_pattern_error", pattern=pattern, error=str(e))


product_cache = CacheClient(prefix="product", ttl=settings.redis_ttl)
category_cache = CacheClient(prefix="category", ttl=settings.redis_ttl)
