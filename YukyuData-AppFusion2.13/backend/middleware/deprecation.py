"""
API Deprecation Middleware
Agrega headers de deprecación a endpoints v0 (/api/*)

Headers agregados a v0 endpoints:
- Deprecation: true
- API-Deprecated: true
- Sunset: Sun, 01 Mar 2026 23:59:59 GMT (fecha de cierre de v0)
- Link: </api/v1/{path}>; rel="successor-version"
- API-Supported-Versions: v0 (deprecated), v1

Migration Plan Phase 1.1 - Added logging for monitoring migration progress.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Track deprecated route usage for migration monitoring
_deprecated_usage_stats: Dict[str, int] = {}


class DeprecationHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade headers de deprecación a endpoints v0.

    Endpoints v0 (/api/*) están marcados como deprecated.
    Los clientes deberían migrar a /api/v1/*

    Sunset date: 01 Mar 2026

    Also logs usage of deprecated routes for monitoring migration progress.
    """

    # Sunset deadline for v0 endpoints
    SUNSET_DATE = "Sat, 01 Mar 2026 23:59:59 GMT"

    async def dispatch(self, request, call_next):
        """Process request and add deprecation headers if applicable"""

        response = await call_next(request)

        # Check if this is a v0 endpoint (matches /api/* but not /api/v*)
        path = request.url.path
        method = request.method
        is_v0_endpoint = (
            path.startswith("/api/") and
            not path.startswith("/api/v1/") and
            not path.startswith("/api/v2/") and
            not path.startswith("/api/v") and
            # Exclude health and docs (not deprecated)
            path not in ["/api/health", "/api/docs", "/api/openapi.json"]
        )

        if is_v0_endpoint:
            # Log deprecated usage for monitoring
            self._log_deprecated_usage(path, method, request)

            # Add deprecation headers
            response.headers["Deprecation"] = "true"
            response.headers["API-Deprecated"] = "true"
            response.headers["Sunset"] = self.SUNSET_DATE

            # Add link to successor version
            v1_path = path.replace("/api/", "/api/v1/")
            response.headers["Link"] = f"<{v1_path}>; rel=\"successor-version\""

            # Add supported versions
            response.headers["API-Supported-Versions"] = "v0 (deprecated), v1"

            # Add warning header (RFC 7234)
            response.headers["Warning"] = (
                '299 - "Deprecated API endpoint. '
                'Migrate to /api/v1/ by 01 Mar 2026."'
            )

        return response

    def _log_deprecated_usage(self, path: str, method: str, request):
        """Log usage of deprecated routes for monitoring migration progress."""
        # Track request count
        key = f"{method}:{path}"
        _deprecated_usage_stats[key] = _deprecated_usage_stats.get(key, 0) + 1
        count = _deprecated_usage_stats[key]

        # Get client info
        client_ip = request.client.host if request.client else "unknown"

        # Log warning (first occurrence and every 100th request to reduce noise)
        if count == 1 or count % 100 == 0:
            logger.warning(
                f"DEPRECATED_API_CALL #{count}: {method} {path} "
                f"(client: {client_ip}) - Migrate to /api/v1/"
            )


def get_deprecated_usage_stats() -> Dict[str, int]:
    """Get current usage statistics for deprecated v0 routes."""
    return dict(_deprecated_usage_stats)


def reset_deprecated_usage_stats():
    """Reset usage statistics (useful for testing)."""
    _deprecated_usage_stats.clear()


class VersionHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware que agrega headers de version API a todas las respuestas.

    También respeta el header Accept-Version del cliente si es proporcionado.
    """

    async def dispatch(self, request, call_next):
        """Process request and add version information"""

        # Get Accept-Version header from client (if provided)
        accept_version = request.headers.get("Accept-Version", "v1")

        # Store in request state for use in endpoints
        request.state.api_version = accept_version

        response = await call_next(request)

        # Add version headers to response
        response.headers["API-Version"] = accept_version
        response.headers["API-Supported-Versions"] = "v0 (deprecated), v1"
        response.headers["X-API-Version"] = "v1"  # Current primary version

        return response
