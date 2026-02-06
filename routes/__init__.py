"""
API Routes Module - YuKyuDATA
=============================

v0 routes have been migrated to v1. Use routes.v1 for all API endpoints.

Response helpers are still available from this module:
    from routes.responses import success_response, error_response
    return success_response(data=employees, message="Data retrieved")

For API routes, use:
    from routes.v1 import router_v1
    app.include_router(router_v1)

Migration completed: 2026-01-22
See docs/MIGRATION_PLAN.md for details.
"""

# Response helpers (still available for use across the application)
from .responses import (
    APIResponse,
    PaginatedResponse,
    success_response,
    error_response,
    paginated_response,
    created_response,
    updated_response,
    deleted_response,
    not_found_response,
    validation_error_response,
    unauthorized_response,
    forbidden_response,
)

# Dependencies module (shared authentication/authorization helpers)
from .dependencies import (
    get_current_user,
)

__all__ = [
    # Response helpers
    "APIResponse",
    "PaginatedResponse",
    "success_response",
    "error_response",
    "paginated_response",
    "created_response",
    "updated_response",
    "deleted_response",
    "not_found_response",
    "validation_error_response",
    "unauthorized_response",
    "forbidden_response",
    # Dependencies
    "get_current_user",
]
