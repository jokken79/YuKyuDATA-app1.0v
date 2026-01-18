"""
API v1 Router Factory
Contiene todos los endpoints versionados en /api/v1/

Estructura:
- Todos los endpoints disponibles en /api/v1/*
- Respuestas estandarizadas con APIResponse
- Paginación mejorada
- Mejor documentación

Usage en main.py:
    from routes.v1 import router_v1
    app.include_router(router_v1)
"""

from fastapi import APIRouter
from .employees import router as employees_router
from .leave_requests import router as leave_requests_router
from .notifications import router as notifications_router
from .yukyu import router as yukyu_router
from .compliance import router as compliance_router
from .compliance_advanced import router as compliance_advanced_router
from .fiscal import router as fiscal_router
from .analytics import router as analytics_router
from .reports import router as reports_router
from .export import router as export_router
from .auth import router as auth_router
from .system import router as system_router
from .health import router as health_router
from .calendar import router as calendar_router
from .genzai import router as genzai_router
from .ukeoi import router as ukeoi_router
from .staff import router as staff_router
from .github import router as github_router

# Create v1 router
router_v1 = APIRouter(prefix="/api/v1", tags=["API v1"])

# Include all v1 routers
router_v1.include_router(auth_router, tags=["Auth v1"])
router_v1.include_router(employees_router, tags=["Employees v1"])
router_v1.include_router(genzai_router, tags=["Genzai v1"])
router_v1.include_router(ukeoi_router, tags=["Ukeoi v1"])
router_v1.include_router(staff_router, tags=["Staff v1"])
router_v1.include_router(leave_requests_router, tags=["Leave Requests v1"])
router_v1.include_router(yukyu_router, tags=["Yukyu v1"])
router_v1.include_router(compliance_router, tags=["Compliance v1"])
router_v1.include_router(compliance_advanced_router, tags=["Compliance (Advanced) v1"])
router_v1.include_router(fiscal_router, tags=["Fiscal v1"])
router_v1.include_router(analytics_router, tags=["Analytics v1"])
router_v1.include_router(reports_router, tags=["Reports v1"])
router_v1.include_router(export_router, tags=["Export v1"])
router_v1.include_router(calendar_router, tags=["Calendar v1"])
router_v1.include_router(notifications_router, tags=["Notifications v1"])
router_v1.include_router(system_router, tags=["System v1"])
router_v1.include_router(health_router, tags=["Health v1"])
router_v1.include_router(github_router, tags=["GitHub v1"])

__all__ = ['router_v1']
