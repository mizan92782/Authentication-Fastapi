from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.security import decode_token
from app.shared.responses.api_response import PaginationParams

bearer_scheme = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────
# 1. AUTH — current logged-in user
# ─────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    Protected route dependency.
    Usage: user = Depends(get_current_user)
    """
    if not credentials:
        raise UnauthorizedException("Missing authentication token")

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as e:
        raise UnauthorizedException(str(e))

    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    from app.modules.users.repository import UserRepository

    user = await UserRepository.get_by_id(payload["sub"])
    if not user or user.is_deleted:
        raise UnauthorizedException("User not found or deactivated")

    return user


# ─────────────────────────────────────────────
# 2. OPTIONAL AUTH — user or None (public routes)
# ─────────────────────────────────────────────
async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """
    Public route that behaves differently for logged-in users.
    Usage: user = Depends(get_optional_user)  → returns user or None
    """
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            return None
        from app.modules.users.repository import UserRepository
        return await UserRepository.get_by_id(payload["sub"])
    except Exception:
        return None


# ─────────────────────────────────────────────
# 3. ROLE CHECK — admin only
# ─────────────────────────────────────────────
async def require_admin(current_user=Depends(get_current_user)):
    """
    Admin-only route dependency.
    Usage: dependencies=[Depends(require_admin)]
    """
    if current_user.role != "admin":
        raise ForbiddenException("Admin access required")
    return current_user


# ─────────────────────────────────────────────
# 4. PAGINATION — page, page_size, search, sort
# ─────────────────────────────────────────────
def get_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Items per page",
    ),
    search: str | None = Query(None, description="Search keyword"),
    sort_by: str | None = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort direction"),
) -> PaginationParams:
    """
    Reusable pagination dependency.
    Usage: params = Depends(get_pagination)
    """
    return PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# ─────────────────────────────────────────────
# 5. REDIS CACHE — get redis client
# ─────────────────────────────────────────────
async def get_cache():
    """
    Redis cache client dependency.
    Usage: cache = Depends(get_cache)
    """
    from app.infrastructure.redis.client import get_redis
    return await get_redis()


# ─────────────────────────────────────────────
# 6. ACTIVE USER — must be active (not banned)
# ─────────────────────────────────────────────
async def get_active_user(current_user=Depends(get_current_user)):
    """
    Ensures the user account is active.
    Usage: user = Depends(get_active_user)
    """
    if not current_user.is_active:
        raise ForbiddenException("Your account has been deactivated")
    return current_user
