import logging
import traceback
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import OperationalError, DisconnectionError, SQLAlchemyError

logger = logging.getLogger(__name__)

async def database_error_handler(request: Request, exc: OperationalError):
    """Handle database connection errors gracefully"""
    # Simply log and return 503
    logger.error(f"Database operational error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database temporarily unavailable"}
    )

async def disconnection_error_handler(request: Request, exc: DisconnectionError):
    """Handle database disconnection errors"""
    logger.error(f"Database disconnection error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database connection lost"}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unhandled errors"""
    logger.error(f"Unhandled exception in {request.method} {request.url}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Validation error"}
    )

def register_error_handlers(app):
    """Register all exception handlers to the app"""
    app.add_exception_handler(OperationalError, database_error_handler)
    app.add_exception_handler(DisconnectionError, disconnection_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("✅ Global error handlers registered")
