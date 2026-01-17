"""
API Routes Module
Contiene todos los endpoints organizados por dominio

Usage in main.py:
    from routes import (
        auth_router, employees_router, leave_requests_router, ...
    )
    app.include_router(auth_router)
    ...

Response helpers:
    from routes.responses import success_response, error_response
    return success_response(data=employees, message="Data retrieved")
"""

# Response helpers
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

# Auth routes
from .auth import router as auth_router

# Employee management routes
from .employees import router as employees_router
from .genzai import router as genzai_router
from .ukeoi import router as ukeoi_router
from .staff import router as staff_router

# Leave management routes
from .leave_requests import router as leave_requests_router
from .yukyu import router as yukyu_router

# Compliance and fiscal routes
from .compliance import router as compliance_router
from .compliance_advanced import router as compliance_advanced_router
from .fiscal import router as fiscal_router

# Analytics and reporting routes
from .analytics import router as analytics_router
from .reports import router as reports_router
from .export import router as export_router

# Calendar and notifications routes
from .calendar import router as calendar_router
from .notifications import router as notifications_router

# System routes
from .system import router as system_router
from .health import router as health_router

# GitHub integration routes
from .github import router as github_router

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
    # Auth
    "auth_router",
    # Employees
    "employees_router",
    "genzai_router",
    "ukeoi_router",
    "staff_router",
    # Leave management
    "leave_requests_router",
    "yukyu_router",
    # Compliance
    "compliance_router",
    "compliance_advanced_router",
    "fiscal_router",
    # Analytics & Reporting
    "analytics_router",
    "reports_router",
    "export_router",
    # Calendar & Notifications
    "calendar_router",
    "notifications_router",
    # System
    "system_router",
    "health_router",
    # GitHub
    "github_router",
]
