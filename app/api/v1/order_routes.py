from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user
from app.core.permissions import require_admin
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=SuccessResponse[OrderResponse], status_code=201)
async def create_order(data: OrderCreate, current_user=Depends(get_current_user)):
    order = await OrderService.create_order(str(current_user.id), data)
    return SuccessResponse(message="Order placed successfully", data=order)


@router.get("/me", response_model=PaginatedResponse[OrderResponse])
async def my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    return await OrderService.get_user_orders(str(current_user.id), page, page_size)


@router.get("/{order_id}", response_model=SuccessResponse[OrderResponse])
async def get_order(order_id: str, current_user=Depends(get_current_user)):
    order = await OrderService.get_order(order_id, str(current_user.id), current_user.role)
    return SuccessResponse(data=order)


@router.patch("/{order_id}/status", response_model=SuccessResponse[OrderResponse], dependencies=[Depends(require_admin)])
async def update_order_status(order_id: str, data: OrderStatusUpdate):
    order = await OrderService.update_status(order_id, data)
    return SuccessResponse(message="Order status updated", data=order)
