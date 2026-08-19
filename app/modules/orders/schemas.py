from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: UUID
    quantity: int


class OrderCreate(BaseModel):
    shipping_address: str
    items: List[OrderItemCreate]
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    status: str
    total_amount: Decimal
    shipping_address: str
    notes: Optional[str]
    items: List[OrderItemResponse] = []

    model_config = {"from_attributes": True}
