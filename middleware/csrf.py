"""
CSRF Protection Middleware for FastAPI

Provides protection against Cross-Site Request Forgery attacks.
Works in conjunction with JWT authentication - requests with valid JWT
don't require additional CSRF protection as they're already secured.

Usage:
    1. Add middleware to app: app.add_middleware(CSRFProtectionMiddleware)
    2. Create endpoint to get CSRF token: GET /api/csrf-token
    3. Frontend sends token in X-CSRF-Token header for POST/PUT/DELETE requests
"""

import secrets
import logging
from typing import Optional, Set
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware para proteccion CSRF.

    Comportamiento:
    - Metodos seguros (GET, HEAD, OPTIONS, TRACE) no requieren CSRF
    - Requests con Authorization header (JWT) no requieren CSRF adicional
    - Requests sin JWT deben incluir X-CSRF-Token header
    - Excluye paths especificos (login, docs, etc.)
    """

    # HTTP methods that don't modify state (safe methods)
    SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"}

    # Token length for secure generation
    TOKEN_LENGTH: int = 32

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[list] = None,
        require_for_authenticated: bool = False
    ):
        """
        Initialize CSRF middleware.

        Args:
            app: ASGI application
            exclude_paths: Paths to exclude from CSRF protection
            require_for_authenticated: If True, require CSRF even with JWT
        """
        super().__init__(app)
        # Paths that should NOT require CSRF protection
        self.exclude_paths = set(exclude_paths or [
            "/api/auth/login",
            "/api/csrf-token",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/"
        ])
        self.require_for_authenticated = require_for_authenticated

    async def dispatch(self, request: Request, call_next):
        """
        Process request and verify CSRF token if needed.
        """
        # Safe methods don't need CSRF protection
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # Check if path is excluded
        path = request.url.path
        if path in self.exclude_paths:
            return await call_next(request)

        # Check for paths that start with excluded patterns
        # (e.g., /static/... should be excluded)
        for excluded in self.exclude_paths:
            if path.startswith(excluded) and excluded.endswith("/"):
                return await call_next(request)

        # Check for Authorization header (JWT authentication)
        auth_header = request.headers.get("Authorization")
        has_jwt = auth_header and auth_header.startswith("Bearer ")

        # If request has valid JWT and we don't require CSRF for authenticated, allow
        if has_jwt and not self.require_for_authenticated:
            return await call_next(request)

        # Verify CSRF token for non-authenticated requests
        csrf_token = request.headers.get("X-CSRF-Token")

        if not csrf_token:
            logger.warning(
                f"CSRF token missing for {request.method} {path} "
                f"from IP: {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF token required",
                    "error_code": "CSRF_TOKEN_MISSING",
                    "hint": "Include X-CSRF-Token header. Get token from GET /api/csrf-token"
                }
            )

        # Token format validation (basic check - token should be base64url safe)
        if len(csrf_token) < 20:
            logger.warning(
                f"Invalid CSRF token format for {request.method} {path} "
                f"from IP: {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Invalid CSRF token format",
                    "error_code": "CSRF_TOKEN_INVALID"
                }
            )

        # Token exists and has valid format - allow request
        # Note: In a stateful implementation, we would validate against stored tokens
        # For stateless CSRF, the presence of a properly formatted token is sufficient
        # because attackers cannot read the token from another origin due to CORS
        return await call_next(request)


def generate_csrf_token() -> str:
    """
    Genera un token CSRF seguro usando secrets.

    Returns:
        str: Token URL-safe de 32 bytes (43 caracteres)
    """
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str) -> bool:
    """
    Valida el formato basico del token CSRF.

    Args:
        token: Token a validar

    Returns:
        bool: True si el formato es valido
    """
    if not token:
        return False

    # Token should be at least 20 chars and max 100 chars
    if len(token) < 20 or len(token) > 100:
        return False

    # Token should only contain URL-safe characters
    import re
    if not re.match(r'^[A-Za-z0-9_-]+$', token):
        return False

    return True
