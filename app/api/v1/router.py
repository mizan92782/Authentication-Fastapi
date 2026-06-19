"""API v1 root router aggregating all route modules."""

from fastapi import APIRouter
from app.api.v1.auth_routes import router as auth_routes


api_v1_router = APIRouter()
api_v1_router.include_router(auth_routes, prefix="/auth", tags=["Auth"])
