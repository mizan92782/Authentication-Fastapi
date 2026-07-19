from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Query
from app.modules.catalog.schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse,
)
from app.modules.catalog.service import CategoryService, ProductService
from app.shared.responses.api_response import SuccessResponse

catalog_router = APIRouter()

# ── Categories ─────────────────────────────────────────────────────────────────

@catalog_router.get("/categories/", response_model=SuccessResponse[List[CategoryResponse]])
async def list_categories():
    data = await CategoryService.list()
    return SuccessResponse(data=data)


@catalog_router.get("/categories/{category_id}/", response_model=SuccessResponse[CategoryResponse])
async def get_category(category_id: UUID):
    return SuccessResponse(data=await CategoryService.get(category_id))


@catalog_router.post("/categories/", response_model=SuccessResponse[CategoryResponse], status_code=201)
async def create_category(data: CategoryCreate):
    return SuccessResponse(message="Category created", data=await CategoryService.create(data))


@catalog_router.patch("/categories/{category_id}/", response_model=SuccessResponse[CategoryResponse])
async def update_category(category_id: UUID, data: CategoryUpdate):
    return SuccessResponse(data=await CategoryService.update(category_id, data))


@catalog_router.delete("/categories/{category_id}/", status_code=204)
async def delete_category(category_id: UUID):
    await CategoryService.delete(category_id)


# ── Products ───────────────────────────────────────────────────────────────────

@catalog_router.get("/products/", response_model=SuccessResponse[List[ProductResponse]])
async def list_products(category_id: Optional[UUID] = Query(None)):
    data = await ProductService.list(category_id)
    return SuccessResponse(data=data)


@catalog_router.get("/products/{product_id}/", response_model=SuccessResponse[ProductResponse])
async def get_product(product_id: UUID):
    return SuccessResponse(data=await ProductService.get(product_id))


@catalog_router.post("/products/", response_model=SuccessResponse[ProductResponse], status_code=201)
async def create_product(data: ProductCreate):
    return SuccessResponse(message="Product created", data=await ProductService.create(data))


@catalog_router.patch("/products/{product_id}/", response_model=SuccessResponse[ProductResponse])
async def update_product(product_id: UUID, data: ProductUpdate):
    return SuccessResponse(data=await ProductService.update(product_id, data))


@catalog_router.delete("/products/{product_id}/", status_code=204)
async def delete_product(product_id: UUID):
    await ProductService.delete(product_id)
