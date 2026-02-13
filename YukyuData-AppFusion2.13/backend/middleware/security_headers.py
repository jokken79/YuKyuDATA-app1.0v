"""
Security Middleware for YuKyuDATA
Includes rate limiting, security headers, and request logging
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from collections import defaultdict
from time import time
from datetime import datetime
from typing import Callable
import logging
import os

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm
    """
    def __init__(
        self,
        app: ASGIApp,
        max_requests: int = 100,
        window_seconds: int = 60,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        # Paths that should NOT be rate limited
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json", "/"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check rate limit before processing request
        """
        # Skip rate limiting in testing mode
        if os.environ.get("TESTING") == "true":
            return await call_next(request)

        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        now = time()
        # Clean old requests outside the window
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window_seconds
        ]

        # Check if limit exceeded
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )

        # Add current request to the list
        self.requests[client_ip].append(now)

        # Process request
        response = await call_next(request)

        # Add remaining requests header
        remaining = max(0, self.max_requests - len(self.requests[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    def __init__(self, app: ASGIApp, security_headers: dict = None):
        super().__init__(app)
        self.security_headers = security_headers or {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)

        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests for auditing
    """
    def __init__(self, app: ASGIApp, log_sensitive: bool = False):
        super().__init__(app)
        self.log_sensitive = log_sensitive

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response"""
        start_time = time()
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        logger.info(
            f"REQUEST {request.method} {request.url.path} "
            f"client_ip={client_ip} "
            f"query_params={dict(request.query_params) if not self.log_sensitive else 'REDACTED'}"
        )

        try:
            response = await call_next(request)
            process_time = time() - start_time

            # Log response
            logger.info(
                f"RESPONSE {request.method} {request.url.path} "
                f"status={response.status_code} "
                f"duration={process_time:.3f}s"
            )

            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time() - start_time
            logger.error(
                f"ERROR {request.method} {request.url.path} "
                f"duration={process_time:.3f}s "
                f"error={str(e)}"
            )
            raise


class AuthenticationLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log authentication attempts
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log auth events"""
        client_ip = request.client.host if request.client else "unknown"

        # Log auth attempts
        if request.url.path == "/api/auth/login":
            logger.info(f"AUTH_ATTEMPT login client_ip={client_ip}")

        response = await call_next(request)

        # Log auth success/failure
        if request.url.path == "/api/auth/login":
            if response.status_code == 200:
                logger.info(f"AUTH_SUCCESS login client_ip={client_ip}")
            else:
                logger.warning(f"AUTH_FAILED login client_ip={client_ip} status={response.status_code}")

        return response
