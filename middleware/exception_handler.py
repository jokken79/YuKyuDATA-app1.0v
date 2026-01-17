"""
Global Exception Handlers for YuKyuDATA API

Provides centralized, consistent error handling for:
- Unhandled exceptions (500 Internal Server Error)
- HTTP exceptions (4xx/5xx errors)
- Request validation errors (422 Validation Error)

Features:
- Structured JSON responses with consistent format
- Request ID tracking for debugging
- Comprehensive logging with stack traces
- Production-safe error messages (no sensitive data leaked)
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """Generate a unique request ID for tracing."""
    return str(uuid.uuid4())[:8]


def get_request_context(request: Request) -> Dict[str, Any]:
    """
    Extract useful context from the request for logging.

    Args:
        request: FastAPI Request object

    Returns:
        Dictionary with request context (method, path, client IP, etc.)
    """
    client_ip = None
    if request.client:
        client_ip = request.client.host

    # Check for forwarded IP (behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    return {
        "method": request.method,
        "path": str(request.url.path),
        "query_params": str(request.query_params) if request.query_params else None,
        "client_ip": client_ip,
        "user_agent": request.headers.get("User-Agent", "")[:200],
    }


def create_error_response(
    status_code: int,
    error: str,
    message: str,
    request_id: str,
    details: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        status_code: HTTP status code
        error: Error type/category
        message: Human-readable error message
        request_id: Unique request identifier for tracing
        details: Additional error details (optional)

    Returns:
        Standardized error response dictionary
    """
    response = {
        "success": False,
        "status": "error",
        "error": error,
        "message": message,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    if details is not None:
        response["details"] = details

    return response


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all unhandled exceptions.

    This catches any exception that wasn't handled by more specific handlers.
    Returns a generic 500 error to avoid leaking sensitive information.

    Args:
        request: FastAPI Request object
        exc: The exception that was raised

    Returns:
        JSONResponse with 500 status code
    """
    request_id = generate_request_id()
    context = get_request_context(request)

    # Log full stack trace for debugging
    logger.error(
        f"Unhandled exception [{request_id}] "
        f"{context['method']} {context['path']} "
        f"from {context['client_ip']}: {exc.__class__.__name__}: {exc}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "exception_type": exc.__class__.__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
            **context
        }
    )

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            status_code=500,
            error="Internal server error",
            message="An unexpected error occurred. Please try again later.",
            request_id=request_id
        ),
        headers={"X-Request-ID": request_id}
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions raised by the application.

    Provides consistent formatting for all HTTP errors (4xx, 5xx).

    Args:
        request: FastAPI Request object
        exc: The HTTPException that was raised

    Returns:
        JSONResponse with the appropriate status code
    """
    request_id = generate_request_id()
    context = get_request_context(request)

    # Determine log level based on status code
    if exc.status_code >= 500:
        logger.error(
            f"HTTP {exc.status_code} [{request_id}] "
            f"{context['method']} {context['path']}: {exc.detail}",
            extra={"request_id": request_id, **context}
        )
    elif exc.status_code >= 400:
        logger.warning(
            f"HTTP {exc.status_code} [{request_id}] "
            f"{context['method']} {context['path']}: {exc.detail}",
            extra={"request_id": request_id, **context}
        )

    # Map status codes to user-friendly error types
    error_type_map = {
        400: "Bad request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not found",
        405: "Method not allowed",
        409: "Conflict",
        422: "Validation error",
        429: "Too many requests",
        500: "Internal server error",
        502: "Bad gateway",
        503: "Service unavailable",
        504: "Gateway timeout"
    }

    error_type = error_type_map.get(exc.status_code, f"HTTP {exc.status_code} error")

    # Use the exception detail as the message
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            error=error_type,
            message=message,
            request_id=request_id
        ),
        headers={"X-Request-ID": request_id}
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors from request parsing.

    Provides detailed error information about which fields failed validation
    and why, making it easier for API consumers to fix their requests.

    Args:
        request: FastAPI Request object
        exc: The RequestValidationError that was raised

    Returns:
        JSONResponse with 422 status code and validation details
    """
    request_id = generate_request_id()
    context = get_request_context(request)

    # Extract and format validation errors
    errors = exc.errors()
    formatted_errors = []

    for error in errors:
        loc = error.get("loc", [])
        # Format location as readable string (e.g., "body.field_name")
        location = ".".join(str(l) for l in loc)

        formatted_errors.append({
            "field": location,
            "type": error.get("type", "unknown"),
            "message": error.get("msg", "Validation failed"),
            "input": _sanitize_input(error.get("input"))
        })

    logger.warning(
        f"Validation error [{request_id}] "
        f"{context['method']} {context['path']}: {len(errors)} error(s)",
        extra={
            "request_id": request_id,
            "validation_errors": formatted_errors,
            **context
        }
    )

    # Create user-friendly summary message
    if len(formatted_errors) == 1:
        field = formatted_errors[0]["field"]
        msg = formatted_errors[0]["message"]
        summary = f"Validation failed for '{field}': {msg}"
    else:
        field_names = [e["field"] for e in formatted_errors[:3]]
        summary = f"Validation failed for fields: {', '.join(field_names)}"
        if len(formatted_errors) > 3:
            summary += f" and {len(formatted_errors) - 3} more"

    return JSONResponse(
        status_code=422,
        content=create_error_response(
            status_code=422,
            error="Validation error",
            message=summary,
            request_id=request_id,
            details=formatted_errors
        ),
        headers={"X-Request-ID": request_id}
    )


async def pydantic_validation_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    Handle pure Pydantic validation errors (not from request parsing).

    This handles ValidationError raised directly in business logic.

    Args:
        request: FastAPI Request object
        exc: The Pydantic ValidationError that was raised

    Returns:
        JSONResponse with 422 status code
    """
    request_id = generate_request_id()
    context = get_request_context(request)

    errors = exc.errors()
    formatted_errors = []

    for error in errors:
        loc = error.get("loc", [])
        location = ".".join(str(l) for l in loc)

        formatted_errors.append({
            "field": location,
            "type": error.get("type", "unknown"),
            "message": error.get("msg", "Validation failed")
        })

    logger.warning(
        f"Pydantic validation error [{request_id}] "
        f"{context['method']} {context['path']}: {len(errors)} error(s)",
        extra={"request_id": request_id, **context}
    )

    return JSONResponse(
        status_code=422,
        content=create_error_response(
            status_code=422,
            error="Validation error",
            message="Data validation failed",
            request_id=request_id,
            details=formatted_errors
        ),
        headers={"X-Request-ID": request_id}
    )


def _sanitize_input(value: Any) -> Any:
    """
    Sanitize input value for logging/response.

    Prevents logging of sensitive data and truncates long values.

    Args:
        value: The input value to sanitize

    Returns:
        Sanitized value safe for logging
    """
    if value is None:
        return None

    # Don't include potentially sensitive field values
    if isinstance(value, str):
        # Truncate long strings
        if len(value) > 100:
            return value[:100] + "..."
        # Check for potentially sensitive data patterns
        lower_val = value.lower()
        if any(pattern in lower_val for pattern in ['password', 'secret', 'token', 'key', 'auth']):
            return "[REDACTED]"
        return value

    if isinstance(value, (int, float, bool)):
        return value

    if isinstance(value, (list, dict)):
        return f"<{type(value).__name__} with {len(value)} items>"

    return f"<{type(value).__name__}>"


def register_exception_handlers(app):
    """
    Register all exception handlers with a FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_handler)

    logger.info("Exception handlers registered successfully")
