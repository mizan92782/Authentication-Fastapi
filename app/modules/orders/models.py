from enum import Enum
from tortoise import fields
from app.shared.base.base_model import BaseModel


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="orders", on_delete=fields.CASCADE)
    status = fields.CharEnumField(enum_type=OrderStatus, max_length=20, default=OrderStatus.PENDING)
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2)
    shipping_address = fields.TextField()
    notes = fields.TextField(null=True)

    class Meta:
        table = "orders"

    def __str__(self):
        return f"Order({self.id}) - {self.status}"


class OrderItem(BaseModel):
    order = fields.ForeignKeyField("models.Order", related_name="items", on_delete=fields.CASCADE)
    product = fields.ForeignKeyField("models.Product", related_name="order_items", on_delete=fields.RESTRICT)
    quantity = fields.IntField()
    unit_price = fields.DecimalField(max_digits=12, decimal_places=2)
    subtotal = fields.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        table = "order_items"
