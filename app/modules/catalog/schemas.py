from __future__ import annotations
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    image: Optional[str]

    model_config = {"from_attributes": True}


# ── Product Image ──────────────────────────────────────────────────────────────

class ProductImageCreate(BaseModel):
    url: str
    alt: Optional[str] = None
    is_primary: bool = False


class ProductImageResponse(BaseModel):
    id: UUID
    url: str
    alt: Optional[str]
    is_primary: bool

    model_config = {"from_attributes": True}


# ── Product ────────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    category_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    price: Decimal
    compare_price: Optional[Decimal] = None
    stock: int = 0
    sku: str
    is_active: bool = True
    images: List[ProductImageCreate] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    compare_price: Optional[Decimal] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    price: Decimal
    compare_price: Optional[Decimal]
    stock: int
    sku: str
    is_active: bool
    category: CategoryResponse
    images: List[ProductImageResponse] = []

    model_config = {"from_attributes": True}
