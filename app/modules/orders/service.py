from decimal import Decimal
from fastapi import HTTPException, status
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.orders.schemas import OrderCreate, OrderItemResponse, OrderResponse
from app.modules.catalog.models import Product


def _item_response(item: OrderItem) -> OrderItemResponse:
    return OrderItemResponse(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product.name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        subtotal=item.subtotal,
    )


def _order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        status=order.status.value,
        total_amount=order.total_amount,
        shipping_address=order.shipping_address,
        notes=order.notes,
        items=[_item_response(i) for i in order.items],
    )


class OrderService:

    @staticmethod
    async def create(user, data: OrderCreate) -> OrderResponse:
        total = Decimal("0")
        line_items = []

        for item in data.items:
            product = await Product.get_or_none(id=item.product_id, is_deleted=False, is_active=True)
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")
            subtotal = product.price * item.quantity
            total += subtotal
            line_items.append((product, item.quantity, product.price, subtotal))

        order = await Order.create(
            user=user,
            total_amount=total,
            shipping_address=data.shipping_address,
            notes=data.notes,
        )
        await OrderItem.bulk_create([
            OrderItem(order=order, product=p, quantity=qty, unit_price=price, subtotal=sub)
            for p, qty, price, sub in line_items
        ])
        # deduct stock
        for p, qty, *_ in line_items:
            p.stock -= qty
            await p.save(update_fields=["stock", "updated_at"])

        return await OrderService.get(str(order.id), user)

    @staticmethod
    async def list_mine(user, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        total = await Order.filter(user=user, is_deleted=False).count()
        orders = await (
            Order.filter(user=user, is_deleted=False)
            .prefetch_related("items__product")
            .order_by("-created_at")
            .offset(offset)
            .limit(page_size)
        )
        return [_order_response(o) for o in orders], total

    @staticmethod
    async def get(order_id: str, user=None, is_admin: bool = False) -> OrderResponse:
        qs = Order.get_or_none(id=order_id, is_deleted=False)
        order = await qs.prefetch_related("items__product")
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if not is_admin and str(order.user_id) != str(user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        return _order_response(order)

    @staticmethod
    async def cancel(order_id: str, user) -> OrderResponse:
        order = await Order.get_or_none(id=order_id, is_deleted=False)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        if str(order.user_id) != str(user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        if order.status not in (OrderStatus.PENDING, OrderStatus.PROCESSING):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order with status '{order.status.value}'"
            )
        order.status = OrderStatus.CANCELLED
        await order.save(update_fields=["status", "updated_at"])
        await order.fetch_related("items__product")
        return _order_response(order)

    @staticmethod
    async def update_status(order_id: str, new_status: str) -> OrderResponse:
        order = await Order.get_or_none(id=order_id, is_deleted=False)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        try:
            order.status = OrderStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
        await order.save(update_fields=["status", "updated_at"])
        await order.fetch_related("items__product")
        return _order_response(order)
