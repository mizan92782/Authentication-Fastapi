import time
from fastapi import HTTPException, Request
from app.infrastructure.redis.client import get_redis


async def non_user_allowed(ip: str, limit: int = 3, window: int = 60):
    redis_client = await get_redis()
    key = f"rate:anon:{ip}"
    now = int(time.time())
    await redis_client.zremrangebyscore(key, 0, now - window)
    count = await redis_client.zcard(key)
    if count >= limit:
        return False
    await redis_client.zadd(key, {str(now): now})
    await redis_client.expire(key, window)
    return True


async def user_allowed(user_id: str, limit: int = 100, window: int = 60):
    redis_client = await get_redis()
    key = f"rate:user:{user_id}"
    now = int(time.time())
    await redis_client.zremrangebyscore(key, 0, now - window)
    count = await redis_client.zcard(key)
    if count >= limit:
        return False
    await redis_client.zadd(key, {str(now): now})
    await redis_client.expire(key, window)
    return True


def rate_limit(limit: int, window: int):
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            redis_client = await get_redis()
            ip = request.client.host
            key = f"rate:decorator:{func.__name__}:{ip}"
            now = int(time.time())
            await redis_client.zremrangebyscore(key, 0, now - window)
            count = await redis_client.zcard(key)
            if count >= limit:
                raise HTTPException(429, "Too many requests")
            await redis_client.zadd(key, {str(now): now})
            await redis_client.expire(key, window)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
    