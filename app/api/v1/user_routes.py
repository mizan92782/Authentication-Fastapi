from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.core.permissions import require_admin
from app.schemas.common import SuccessResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_me(current_user=Depends(get_current_user)):
    return SuccessResponse(data=UserResponse.model_validate(current_user))


@router.patch("/me", response_model=SuccessResponse[UserResponse])
async def update_me(data: UserUpdate, current_user=Depends(get_current_user)):
    user = await UserService.update(str(current_user.id), data)
    return SuccessResponse(message="Profile updated", data=user)


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse], dependencies=[Depends(require_admin)])
async def get_user(user_id: str):
    user = await UserService.get_by_id(user_id)
    return SuccessResponse(data=user)


@router.delete("/{user_id}", dependencies=[Depends(require_admin)], status_code=204)
async def delete_user(user_id: str):
    await UserService.delete(user_id)
