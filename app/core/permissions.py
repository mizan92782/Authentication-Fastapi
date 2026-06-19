from enum import StrEnum
from fastapi import Depends, HTTPException, status
from app.core.dependencies import get_current_user


class Role(StrEnum):
    ADMIN = "admin"
    CUSTOMER = "customer"


def require_roles(*roles: Role):
    """Dependency factory — raises 403 if current user lacks required role."""

    async def _check(current_user=Depends(get_current_user)):
        if current_user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check


require_admin = require_roles(Role.ADMIN)
require_customer = require_roles(Role.CUSTOMER, Role.ADMIN)
