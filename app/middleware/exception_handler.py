from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from tortoise.exceptions import DoesNotExist, IntegrityError
from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.detail, "errors": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"success": False, "message": "Validation error", "errors": errors},
        )

    @app.exception_handler(DoesNotExist)
    async def does_not_exist_handler(request: Request, exc: DoesNotExist):
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Resource not found", "errors": None},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error("db_integrity_error", error=str(exc))
        return JSONResponse(
            status_code=409,
            content={"success": False, "message": "Data conflict error", "errors": None},
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError):
        errors = [{"field": e["loc"][-1] if e["loc"] else "non_field_errors", "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"success": False, "message": "Validation error", "errors": errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error", "errors": None},
        )
