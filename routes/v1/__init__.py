"""
API v1 Routes - Modern Versioned Endpoints

FASE 3: API Versioning with backward compatibility.

This module provides v1 endpoints with:
- Repository-based data access
- Dependency injection
- Standard response formats
- Comprehensive error handling

Migration Path from v0 (unversioned) to v1:
1. Old: GET /api/employees
   New: GET /api/v1/employees
2. Response format is identical for backward compatibility
3. Redirect: Old endpoints redirect to /api/v1/*

Endpoints:
- /api/v1/employees
- /api/v1/leave-requests
- /api/v1/notifications
- /api/v1/users
- /api/v1/yukyu
- etc.

Headers:
- Accept-Version: v1 (optional, defaults to v1)
- X-API-Key: for authentication

Responses:
- All responses follow standard format
- Error responses include error codes
- Pagination included for list endpoints
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["v1"])

__all__ = ["router"]
