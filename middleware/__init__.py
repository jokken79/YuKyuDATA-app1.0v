"""
Middleware Module
Contiene middleware personalizado para la aplicacion
"""

from .rate_limiter import (
    RateLimiter,
    UserAwareRateLimiter,
    RateLimitMiddleware as RateLimiterMiddleware,
    RateLimitInfo,
    user_aware_limiter,
    check_rate_limit,
    get_rate_limit_headers,
    RATE_LIMITS,
)
from .security import verify_token, get_current_user
from .exception_handler import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_handler,
    register_exception_handlers,
    generate_request_id,
    create_error_response,
)
from .csrf import (
    CSRFProtectionMiddleware,
    generate_csrf_token,
    validate_csrf_token,
)
from .security_headers import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    AuthenticationLoggingMiddleware,
)

__all__ = [
    # Rate Limiter
    "RateLimiter",
    "UserAwareRateLimiter",
    "RateLimiterMiddleware",
    "RateLimitInfo",
    "user_aware_limiter",
    "check_rate_limit",
    "get_rate_limit_headers",
    "RATE_LIMITS",
    # Security
    "verify_token",
    "get_current_user",
    # Exception handlers
    "global_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "pydantic_validation_handler",
    "register_exception_handlers",
    "generate_request_id",
    "create_error_response",
    # CSRF
    "CSRFProtectionMiddleware",
    "generate_csrf_token",
    "validate_csrf_token",
    # Security headers
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "RequestLoggingMiddleware",
    "AuthenticationLoggingMiddleware",
]
