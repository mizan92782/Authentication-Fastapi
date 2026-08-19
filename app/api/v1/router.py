"""API v1 root router aggregating all route modules."""

from fastapi import APIRouter
from app.api.v1.auth_routes import auth_router
from app.api.v1.catalog_routes import catalog_router
from app.api.v1.ai_routes import ai_router
from app.api.v1.order_routes import order_router


api_v1_router = APIRouter()
api_v1_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(catalog_router, prefix="/catalog", tags=["Catalog"])
api_v1_router.include_router(order_router, prefix="/orders", tags=["Orders"])
api_v1_router.include_router(ai_router, prefix="/ai", tags=["AI"])
