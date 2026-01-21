from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from collections import defaultdict
from time import time
import uvicorn
import shutil
import os
import jwt
from pathlib import Path
from datetime import datetime, timedelta, date, timezone

# Local modules
import database
from services import excel_service
from utils.logger import logger, log_api_request, log_db_operation, log_sync_event, log_leave_request
from services.search_service import SearchService
from services.auth import (
    create_access_token,
    verify_token,
    get_current_user,
    get_admin_user,
    authenticate_user,
    check_rate_limit,
    CurrentUser,
    UserLogin as AuthUserLogin
)
from config.security import settings, validate_security_config
from config.secrets_validation import validate_secrets, print_secrets_status
from middleware.security_headers import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    AuthenticationLoggingMiddleware
)
from middleware.exception_handler import register_exception_handlers
from middleware.csrf import CSRFProtectionMiddleware, generate_csrf_token
from utils.pagination import PaginationParams, PaginatedResponse, paginate_list
from services.caching import cached, invalidate_employee_cache, get_cache_stats
from services.fiscal_year import (
    process_year_end_carryover,
    get_employee_balance_breakdown,
    check_expiring_soon,
    check_5day_compliance,
    get_grant_recommendation,
    calculate_seniority_years,
    calculate_granted_days,
    get_fiscal_period,
    apply_lifo_deduction,
    FISCAL_CONFIG,
    GRANT_TABLE
)
from services.excel_export import (
    create_approved_requests_excel,
    create_monthly_report_excel,
    create_annual_ledger_excel,
    update_master_excel,
    get_export_files,
    cleanup_old_exports,
    EXPORT_DIR
)
from services.reports import (
    ReportGenerator,
    save_report,
    list_reports,
    cleanup_old_reports,
    REPORTS_DIR
)
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import API routers from routes module
from routes import (
    auth_router,
    employees_router,
    genzai_router,
    ukeoi_router,
    staff_router,
    leave_requests_router,
    yukyu_router,
    compliance_router,
    compliance_advanced_router,
    fiscal_router,
    analytics_router,
    reports_router,
    export_router,
    calendar_router,
    notifications_router,
    system_router,
    health_router,
    github_router,
)

# Import v1 router
from routes.v1 import router_v1

# Import middleware for API versioning
from middleware.deprecation import DeprecationHeaderMiddleware, VersionHeaderMiddleware

# ============================================
# ASYNC EXECUTOR FOR EXCEL PARSING
# ============================================
# Global thread pool executor for CPU-bound Excel operations
# This prevents blocking the event loop during heavy parsing
_excel_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="excel_parser")


# Import audit logger utilities
from utils.audit_logger import audit_action, log_audit_action, get_client_info


# Import Pydantic models
from models.leave_request import LeaveRequestCreate
from models.vacation import UsageDetailCreate, UsageDetailUpdate
from models.employee import EmployeeUpdate, BulkUpdateRequest, BulkUpdatePreview
from models.common import DateRangeQuery


# ============================================
# RATE LIMITER
# ============================================

from utils.rate_limiter import RateLimiter, rate_limiter


# ============================================
# JWT AUTHENTICATION SYSTEM (Using config.security)
# ============================================

# Validate security configuration on startup
_security_issues = validate_security_config()
if _security_issues and not settings.debug:
    logger.error("SECURITY CONFIGURATION ISSUES DETECTED:")
    for issue in _security_issues:
        logger.error(f"  ⚠️  {issue}")
    # In production, this would exit the app
    # But allow development to proceed with warnings

# Security
security = HTTPBearer(auto_error=False)


# TokenResponse model (from auth module)
class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


# ============================================
# APP INITIALIZATION
# ============================================

app = FastAPI(
    title="YuKyu Dashboard API",
    description="""
    ## Employee Paid Leave Management System (有給休暇管理システム)

    Sistema completo de gestión de vacaciones pagadas conforme a la normativa japonesa.

    ### Características Principales

    * **Gestión de Vacaciones**: Seguimiento de días otorgados, usados y balance
    * **Solicitudes de Ausencia**: Flujo de aprobación de solicitudes
    * **Cumplimiento Legal**: Verificación automática de 5 días obligatorios
    * **Reportes**: Generación de reportes mensuales y anuales
    * **Sincronización Excel**: Carga bidireccional desde archivos Excel
    * **Registro de Empleados**: Gestión de empleados Genzai (派遣) y Ukeoi (請負)

    ### Normativa

    Cumple con el Labor Standards Act Article 39 de Japón y reforma laboral de 2019.

    ### Autenticación

    La API utiliza JWT Bearer tokens. Usa `/api/auth/login` para obtener un token.
    """,
    version="2.4.0",
    contact={
        "name": "YuKyuDATA Support",
        "email": "support@yukyu.example.com"
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=[
        {"name": "Authentication", "description": "Autenticación y gestión de tokens JWT"},
        {"name": "Employees", "description": "Gestión de datos de empleados y vacaciones"},
        {"name": "Leave Requests", "description": "Solicitudes de vacaciones y aprobaciones"},
        {"name": "Compliance", "description": "Verificaciones de cumplimiento normativo"},
        {"name": "Analytics", "description": "Análisis y KPIs de uso de vacaciones"},
        {"name": "Reports", "description": "Generación de reportes Excel y PDF"},
        {"name": "Genzai", "description": "Gestión de empleados dispatch (派遣社員)"},
        {"name": "Ukeoi", "description": "Gestión de empleados contrato (請負社員)"},
        {"name": "System", "description": "Información del sistema y diagnóstico"},
    ],
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    openapi_url="/openapi.json"
)

# Configure CORS - Restricted to specific origins
# Get ports from environment variables (defaults for safe fallback)
SERVER_PORT = int(os.getenv("PORT", "8000"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3000"))

ALLOWED_ORIGINS = [
    f"http://localhost:{SERVER_PORT}",
    f"http://127.0.0.1:{SERVER_PORT}",
    f"http://localhost:{FRONTEND_PORT}",
    f"http://127.0.0.1:{FRONTEND_PORT}",
    # Also allow standard ports just in case
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

logger.info(f"CORS Configured for Server Port: {SERVER_PORT}, Frontend Port: {FRONTEND_PORT}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # Changed to True to allow cookies/auth headers if needed
    allow_methods=["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["*"],     # Allow all headers including Authorization
)

# Add security middlewares
app.add_middleware(
    AuthenticationLoggingMiddleware
)
app.add_middleware(
    RequestLoggingMiddleware,
    log_sensitive=settings.log_request_headers
)
app.add_middleware(
    SecurityHeadersMiddleware,
    security_headers=settings.security_headers
)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    # ✅ FIX 2: /api/auth/login is now rate limited (5/min in RATE_LIMITS config)
    exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/", "/static"]
)

# Add CSRF protection middleware
# Note: Requests with JWT Authorization header don't require CSRF token
app.add_middleware(
    CSRFProtectionMiddleware,
    exclude_paths=[
        "/api/auth/login",
        "/api/csrf-token",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/"
    ],
    require_for_authenticated=False  # JWT-authenticated requests don't need CSRF
)

# Add GZIP compression middleware for performance
# Compresses responses > 500 bytes for faster transfer
app.add_middleware(GZipMiddleware, minimum_size=500)

# Add API versioning middlewares
# VersionHeaderMiddleware: Adds API-Version headers to all responses
# DeprecationHeaderMiddleware: Adds deprecation warnings to v0 endpoints
app.add_middleware(VersionHeaderMiddleware)
app.add_middleware(DeprecationHeaderMiddleware)

# ============================================
# GLOBAL EXCEPTION HANDLERS
# ============================================
# Register centralized exception handlers for consistent error responses
# Provides: request_id tracking, structured JSON errors, comprehensive logging
register_exception_handlers(app)

# Constants - Relative paths from project directory
PROJECT_DIR = Path(__file__).parent  # Directorio del proyecto
E_DRIVE_EXCEL_PATH = Path("E:/CosasParaAppsJp/有給休暇管理.xlsm")
DEFAULT_EXCEL_PATH = E_DRIVE_EXCEL_PATH if E_DRIVE_EXCEL_PATH.exists() else PROJECT_DIR / "有給休暇管理.xlsm"
EMPLOYEE_REGISTRY_PATH = PROJECT_DIR / "【新】社員台帳(UNS)T　2022.04.05～.xlsm"
UPLOAD_DIR = PROJECT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize Database
database.init_db()

# ============================================
# ============================================
# APP LIFECYCLE MANAGEMENT
# ============================================

# Register startup/shutdown events
from services.lifecycle import register_lifecycle_events
register_lifecycle_events(app)

# Get base directory for Vercel compatibility
BASE_DIR = Path(__file__).resolve().parent

# Mount static files (css, js, etc.)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ============================================
# REGISTER API ROUTERS
# ============================================
# All modular routes are defined in routes/ directory
app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(genzai_router)
app.include_router(ukeoi_router)
app.include_router(staff_router)
app.include_router(leave_requests_router)
app.include_router(yukyu_router)
app.include_router(compliance_router)
app.include_router(compliance_advanced_router)
app.include_router(fiscal_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(export_router)
app.include_router(calendar_router)
app.include_router(notifications_router)
app.include_router(system_router)
app.include_router(health_router)
app.include_router(github_router)

# Include v1 API router (all endpoints available at /api/v1/*)
app.include_router(router_v1)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main dashboard page."""
    template_path = BASE_DIR / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================
# CSRF TOKEN ENDPOINT
# ============================================
# Note: All other authentication endpoints are in routes/auth.py

@app.get("/api/csrf-token", tags=["Authentication"])
async def get_csrf_token():
    """
    Generate a CSRF token for non-authenticated requests.

    Frontend should:
    1. Call this endpoint to get a token
    2. Include token in X-CSRF-Token header for POST/PUT/DELETE requests
    3. Token is not required if Authorization header (JWT) is present

    Returns:
        dict: CSRF token and usage instructions
    """
    token = generate_csrf_token()
    return {
        "csrf_token": token,
        "header_name": "X-CSRF-Token",
        "expires_in": 3600,  # Recommended to refresh every hour
        "note": "Include this token in X-CSRF-Token header for POST/PUT/DELETE requests. Not required if using JWT authentication."
    }


# ============================================
# MAIN ENTRY POINT
# ============================================
# NOTE: All API endpoints have been moved to routes/ directory
# This file now only contains:
# - App initialization and middleware configuration
# - "/" endpoint (serves index.html)
# - "/api/csrf-token" endpoint (CSRF token generation)
# All other endpoints are in routes/*.py and registered via include_router


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8765))
    logger.info(f"Starting YuKyuDATA-app server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


# === END OF FILE ===
# The following code has been removed as it was duplicated in routes/
# See routes/ directory for all API endpoints
