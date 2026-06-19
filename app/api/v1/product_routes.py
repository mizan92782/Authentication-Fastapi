from fastapi import APIRouter, Depends, Query
from typing import Optional
from decimal import Decimal
import uuid
from app.core.permissions import require_admin
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.product import ProductCreate, ProductFilterParams, ProductResponse, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    in_stock: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    params = ProductFilterParams(
        page=page, page_size=page_size, search=search,
        category_id=category_id, min_price=min_price, max_price=max_price,
        in_stock=in_stock, sort_by=sort_by, sort_order=sort_order,
    )
    return await ProductService.list_products(params)


@router.get("/{product_id}", response_model=SuccessResponse[ProductResponse])
async def get_product(product_id: str):
    product = await ProductService.get_by_id(product_id)
    return SuccessResponse(data=product)


@router.post("", response_model=SuccessResponse[ProductResponse], status_code=201, dependencies=[Depends(require_admin)])
async def create_product(data: ProductCreate):
    product = await ProductService.create(data)
    return SuccessResponse(message="Product created", data=product)


@router.patch("/{product_id}", response_model=SuccessResponse[ProductResponse], dependencies=[Depends(require_admin)])
async def update_product(product_id: str, data: ProductUpdate):
    product = await ProductService.update(product_id, data)
    return SuccessResponse(message="Product updated", data=product)


@router.delete("/{product_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_product(product_id: str):
    await ProductService.delete(product_id)
