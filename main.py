from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

from app.api.v1.router import api_v1_router
from app.infrastructure.redis.client import close_redis
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import close_db, init_db
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.request_logging import RequestLoggingMiddleware

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)


# Routes
app.include_router(api_v1_router)



@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
