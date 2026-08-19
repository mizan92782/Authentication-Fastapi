from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user, require_admin
from app.modules.orders.schemas import OrderCreate, OrderResponse
from app.modules.orders.service import OrderService
from app.shared.responses.api_response import SuccessResponse, PaginatedResponse
import math

order_router = APIRouter()


@order_router.post("/", response_model=SuccessResponse[OrderResponse], status_code=201)
async def create_order(data: OrderCreate, current_user=Depends(get_current_user)):
    order = await OrderService.create(current_user, data)
    return SuccessResponse(message="Order placed successfully", data=order)


@order_router.get("/me/", response_model=PaginatedResponse[OrderResponse])
async def my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
):
    orders, total = await OrderService.list_mine(current_user, page, page_size)
    return PaginatedResponse(
        data=orders,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


@order_router.get("/{order_id}/", response_model=SuccessResponse[OrderResponse])
async def get_order(order_id: str, current_user=Depends(get_current_user)):
    order = await OrderService.get(order_id, user=current_user)
    return SuccessResponse(data=order)


@order_router.post("/{order_id}/cancel/", response_model=SuccessResponse[OrderResponse])
async def cancel_order(order_id: str, current_user=Depends(get_current_user)):
    order = await OrderService.cancel(order_id, current_user)
    return SuccessResponse(message="Order cancelled", data=order)


@order_router.patch("/{order_id}/status/", response_model=SuccessResponse[OrderResponse])
async def update_order_status(
    order_id: str,
    status: str,
    _=Depends(require_admin),
):
    order = await OrderService.update_status(order_id, status)
    return SuccessResponse(message="Order status updated", data=order)
