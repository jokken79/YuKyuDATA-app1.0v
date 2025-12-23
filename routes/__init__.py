"""
API Routes Module
Contiene todos los endpoints organizados por dominio
"""

from .auth import router as auth_router
from .employees import router as employees_router
from .leave_requests import router as leave_requests_router
from .compliance import router as compliance_router
from .analytics import router as analytics_router
from .reports import router as reports_router
from .genzai import router as genzai_router
from .ukeoi import router as ukeoi_router
from .system import router as system_router

__all__ = [
    "auth_router",
    "employees_router",
    "leave_requests_router",
    "compliance_router",
    "analytics_router",
    "reports_router",
    "genzai_router",
    "ukeoi_router",
    "system_router",
]
