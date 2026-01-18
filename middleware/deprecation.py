"""
API Deprecation Middleware
Agrega headers de deprecación a endpoints v0 (/api/*)

Headers agregados a v0 endpoints:
- Deprecation: true
- API-Deprecated: true
- Sunset: Sun, 31 Mar 2026 23:59:59 GMT (fecha de cierre de v0)
- Link: </api/v1/{path}>; rel="successor-version"
- API-Supported-Versions: v0 (deprecated), v1
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from datetime import datetime


class DeprecationHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade headers de deprecación a endpoints v0.
    
    Endpoints v0 (/api/*) están marcados como deprecated.
    Los clientes deberían migrar a /api/v1/*
    
    Sunset date: 31 Mar 2026
    """
    
    # Sunset deadline for v0 endpoints
    SUNSET_DATE = "Sun, 31 Mar 2026 23:59:59 GMT"
    
    async def dispatch(self, request, call_next):
        """Process request and add deprecation headers if applicable"""
        
        response = await call_next(request)
        
        # Check if this is a v0 endpoint (matches /api/* but not /api/v*)
        path = request.url.path
        is_v0_endpoint = (
            path.startswith("/api/") and
            not path.startswith("/api/v1/") and
            not path.startswith("/api/v2/") and
            not path.startswith("/api/v")
        )
        
        if is_v0_endpoint:
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
                'Migrate to /api/v1/ by 31 Mar 2026."'
            )
        
        return response


class VersionHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware que agrega headers de versión API a todas las respuestas.
    
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
