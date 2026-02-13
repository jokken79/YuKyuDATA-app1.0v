"""
Error Handler Middleware
Centralized error handling and HTTP response transformation
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from exceptions.custom_exceptions import (
    YuKyuException,
    EmployeeNotFoundException,
    InvalidDataException,
    AuthenticationException,
    AuthorizationException,
    DatabaseException,
    ValidationException,
    ResourceNotFoundException,
    ExcelParseException,
    SyncException,
    RateLimitException
)

logger = logging.getLogger(__name__)


async def yukyu_exception_handler(request: Request, exc: YuKyuException) -> JSONResponse:
    """
    Handle custom YuKyuDATA exceptions
    
    Maps custom exceptions to appropriate HTTP status codes
    """
    # Determine status code based on exception type
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if isinstance(exc, (EmployeeNotFoundException, ResourceNotFoundException)):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (InvalidDataException, ValidationException, ExcelParseException)):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, AuthenticationException):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, AuthorizationException):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, RateLimitException):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, (DatabaseException, SyncException)):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # Log the error
    logger.error(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )
    
    # Create response
    response_data = {
        "error": exc.__class__.__name__,
        "message": exc.message,
        "path": request.url.path
    }
    
    # Add details if available (but sanitize in production)
    if exc.details and hasattr(exc, 'details'):
        response_data["details"] = exc.details
    
    # Add retry_after header for rate limit
    headers = {}
    if isinstance(exc, RateLimitException):
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=status_code,
        content=response_data,
        headers=headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors
    Returns detailed field-level validation errors
    """
    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle standard HTTP exceptions
    """
    logger.warning(
        f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "path": request.url.path
        },
        headers=getattr(exc, 'headers', None)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions
    Prevents internal details from leaking in production
    """
    logger.exception(
        f"Unhandled exception on {request.url.path}",
        exc_info=exc
    )
    
    # In production, don't expose internal error details
    # In development, show full error for debugging
    import os
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    if debug_mode:
        response_data = {
            "error": "InternalServerError",
            "message": str(exc),
            "type": exc.__class__.__name__,
            "path": request.url.path
        }
    else:
        response_data = {
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "path": request.url.path
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    # Custom exceptions
    app.add_exception_handler(YuKyuException, yukyu_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Catch-all
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered")
