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


# ============================================
# AUDIT LOG HELPER FUNCTIONS
# ============================================

def get_client_info(request: Request) -> dict:
    """Extrae informacion del cliente desde el Request de FastAPI."""
    client_ip = request.client.host if request.client else None

    # Intentar obtener IP real si esta detras de proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent", "")

    return {
        "ip_address": client_ip,
        "user_agent": user_agent[:500] if user_agent else None  # Limitar longitud
    }


def audit_action(action: str, entity_type: str, get_entity_id=None, get_old_value=None):
    """
    Decorador para registrar automaticamente acciones en el audit log.

    Args:
        action: Tipo de accion (CREATE, UPDATE, DELETE, APPROVE, REJECT, etc.)
        entity_type: Tipo de entidad (employee, leave_request, yukyu_usage, etc.)
        get_entity_id: Funcion para extraer entity_id de los argumentos
        get_old_value: Funcion async para obtener el valor anterior (para UPDATE/DELETE)

    Ejemplo de uso:
        @audit_action("UPDATE", "yukyu_usage", get_entity_id=lambda args, kwargs: kwargs.get('detail_id'))
        async def update_usage_detail(detail_id: int, update_data: UsageDetailUpdate):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Intentar extraer request del contexto
            request = kwargs.get('request')
            user = kwargs.get('user')

            # Obtener info del cliente
            client_info = {}
            if request:
                client_info = get_client_info(request)

            # Obtener user_id
            user_id = None
            if user:
                if hasattr(user, 'username'):
                    user_id = user.username
                elif isinstance(user, dict):
                    user_id = user.get('username')

            # Obtener entity_id
            entity_id = None
            if get_entity_id:
                try:
                    entity_id = get_entity_id(args, kwargs)
                    if entity_id is not None:
                        entity_id = str(entity_id)
                except Exception:
                    pass

            # Obtener old_value para UPDATE/DELETE
            old_value = None
            if get_old_value and action in ["UPDATE", "DELETE"]:
                try:
                    if asyncio.iscoroutinefunction(get_old_value):
                        old_value = await get_old_value(args, kwargs)
                    else:
                        old_value = get_old_value(args, kwargs)
                except Exception:
                    pass

            # Ejecutar la funcion original
            result = await func(*args, **kwargs)

            # Determinar new_value del resultado
            new_value = None
            if isinstance(result, dict):
                # Buscar datos relevantes en el resultado
                for key in ['updated_record', 'created_record', 'deleted_record', 'updated_employee', 'data']:
                    if key in result:
                        new_value = result[key]
                        break
                if new_value is None and action == "CREATE":
                    new_value = result

            # Registrar en audit log
            try:
                database.log_audit(
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    old_value=old_value,
                    new_value=new_value,
                    user_id=user_id,
                    ip_address=client_info.get('ip_address'),
                    user_agent=client_info.get('user_agent')
                )
            except Exception as e:
                logger.warning(f"Failed to log audit: {str(e)}")

            return result
        return wrapper
    return decorator


async def log_audit_action(
    request: Request,
    action: str,
    entity_type: str,
    entity_id: str = None,
    old_value = None,
    new_value = None,
    user = None,
    additional_info: dict = None
):
    """
    Funcion auxiliar para registrar manualmente una accion en el audit log.
    Util cuando el decorador no es practico.
    """
    client_info = get_client_info(request)

    user_id = None
    if user:
        if hasattr(user, 'username'):
            user_id = user.username
        elif isinstance(user, dict):
            user_id = user.get('username')

    try:
        audit_id = database.log_audit(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            old_value=old_value,
            new_value=new_value,
            user_id=user_id,
            ip_address=client_info.get('ip_address'),
            user_agent=client_info.get('user_agent'),
            additional_info=additional_info
        )
        return audit_id
    except Exception as e:
        logger.warning(f"Failed to log audit: {str(e)}")
        return None


# ============================================
# PYDANTIC MODELS FOR VALIDATION
# ============================================

class LeaveRequestCreate(BaseModel):
    employee_num: str = Field(..., min_length=1, description="Employee number")
    employee_name: str = Field(..., min_length=1, description="Employee name")
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: str = Field(..., description="End date YYYY-MM-DD")
    days_requested: float = Field(..., ge=0, le=40, description="Days requested")
    hours_requested: float = Field(0, ge=0, le=320, description="Hours requested")
    leave_type: str = Field(..., description="Leave type: full, half_am, half_pm, hourly")
    reason: Optional[str] = None

    @field_validator('leave_type')
    @classmethod
    def validate_leave_type(cls, v):
        valid_types = ['full', 'half_am', 'half_pm', 'hourly']
        if v not in valid_types:
            raise ValueError(f'leave_type must be one of: {valid_types}')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError('end_date must be after start_date')
        return v


class DateRangeQuery(BaseModel):
    start_date: str
    end_date: str


# === EDIT YUKYU DATA MODELS (v2.1) ===

class UsageDetailUpdate(BaseModel):
    """Modelo para actualizar un registro de uso de yukyu."""
    days_used: Optional[float] = Field(None, ge=0.25, le=1.0, description="Días usados (0.25, 0.5, 1.0)")
    use_date: Optional[str] = Field(None, description="Nueva fecha YYYY-MM-DD")

    @field_validator('days_used')
    @classmethod
    def validate_days(cls, v):
        if v is not None:
            valid_values = [0.25, 0.5, 0.75, 1.0]
            if v not in valid_values:
                raise ValueError(f'days_used debe ser: {valid_values} (0.5 = medio día)')
        return v


class UsageDetailCreate(BaseModel):
    """Modelo para crear un nuevo registro de uso de yukyu."""
    employee_num: str = Field(..., min_length=1, description="Número de empleado")
    name: str = Field(..., min_length=1, description="Nombre del empleado")
    use_date: str = Field(..., description="Fecha de uso YYYY-MM-DD")
    days_used: float = Field(1.0, ge=0.25, le=1.0, description="Días usados")

    @field_validator('days_used')
    @classmethod
    def validate_days(cls, v):
        valid_values = [0.25, 0.5, 0.75, 1.0]
        if v not in valid_values:
            raise ValueError(f'days_used debe ser: {valid_values} (0.5 = medio día)')
        return v


class EmployeeUpdate(BaseModel):
    """Modelo para actualizar datos de empleado."""
    name: Optional[str] = None
    haken: Optional[str] = None
    granted: Optional[float] = Field(None, ge=0, le=40)
    used: Optional[float] = Field(None, ge=0, le=40)
    validate_limit: bool = True  # Validar límite de 40 días acumulados


# === BULK UPDATE MODEL (v2.3) ===

class BulkUpdateRequest(BaseModel):
    """Modelo para actualizar multiples empleados en una operacion."""
    employee_nums: List[str] = Field(..., min_length=1, max_length=50,
                                      description="Lista de numeros de empleado (max 50)")
    year: int = Field(..., ge=2000, le=2100, description="Año fiscal")
    updates: dict = Field(..., description="Campos a actualizar")
    validate_limit: bool = True  # Validar límite de 40 días acumulados

    @field_validator('employee_nums')
    @classmethod
    def validate_employee_nums(cls, v):
        if len(v) > 50:
            raise ValueError('Maximo 50 empleados por operacion')
        if len(v) == 0:
            raise ValueError('Se requiere al menos un empleado')
        return v

    @field_validator('updates')
    @classmethod
    def validate_updates(cls, v):
        if not v:
            raise ValueError('Se requiere al menos un campo a actualizar')
        valid_fields = {'add_granted', 'add_used', 'set_haken', 'set_granted', 'set_used'}
        invalid = set(v.keys()) - valid_fields
        if invalid:
            raise ValueError(f'Campos invalidos: {invalid}. Validos: {valid_fields}')
        return v


class BulkUpdatePreview(BaseModel):
    """Modelo para previsualizar cambios de bulk update."""
    employee_nums: List[str] = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=2000, le=2100)
    updates: dict


# ============================================
# RATE LIMITER
# ============================================

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time()
        # Clean old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window
        ]

        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        self.requests[client_ip].append(now)
        return True

    def get_remaining(self, client_ip: str) -> int:
        now = time()
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < self.window
        ]
        return max(0, self.max_requests - len(self.requests[client_ip]))


rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


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
DEFAULT_EXCEL_PATH = PROJECT_DIR / "有給休暇管理.xlsm"
EMPLOYEE_REGISTRY_PATH = PROJECT_DIR / "【新】社員台帳(UNS)T　2022.04.05～.xlsm"
UPLOAD_DIR = PROJECT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize Database
database.init_db()

# ============================================
# AUTO-SYNC ON STARTUP IF DATABASE IS EMPTY
# ============================================
def auto_sync_on_startup():
    """
    Sincroniza automáticamente los datos desde Excel si la base de datos está vacía.
    Esto asegura que los datos persisten y no hay que sincronizar manualmente cada vez.
    También crea un backup automático si la BD tiene datos.
    """
    try:
        # Check if employees table is empty
        employees = database.get_employees()

        # If database has data, create automatic backup on startup
        if len(employees) > 0:
            try:
                backup_result = database.create_backup()
                logger.info(f"🔒 Auto-backup created: {backup_result['filename']}")
            except Exception as backup_err:
                logger.warning(f"⚠️ Auto-backup failed (non-critical): {str(backup_err)}")

        if len(employees) == 0:
            logger.info("📊 Database is empty - attempting auto-sync from Excel...")

            # Try to sync vacation data
            if DEFAULT_EXCEL_PATH.exists():
                logger.info(f"📁 Found vacation Excel: {DEFAULT_EXCEL_PATH}")
                data = excel_service.parse_excel_file(DEFAULT_EXCEL_PATH)
                database.save_employees(data)

                # Also parse usage details
                usage_details = excel_service.parse_yukyu_usage_details(DEFAULT_EXCEL_PATH)
                database.save_yukyu_usage_details(usage_details)

                logger.info(f"✅ Auto-synced {len(data)} employees + {len(usage_details)} usage details")
            else:
                logger.warning(f"⚠️ Vacation Excel not found at: {DEFAULT_EXCEL_PATH}")

            # Try to sync Genzai (dispatch employees)
            if EMPLOYEE_REGISTRY_PATH.exists():
                logger.info(f"📁 Found employee registry: {EMPLOYEE_REGISTRY_PATH}")

                genzai_data = excel_service.parse_genzai_sheet(EMPLOYEE_REGISTRY_PATH)
                database.save_genzai(genzai_data)
                logger.info(f"✅ Auto-synced {len(genzai_data)} dispatch employees (Genzai)")

                ukeoi_data = excel_service.parse_ukeoi_sheet(EMPLOYEE_REGISTRY_PATH)
                database.save_ukeoi(ukeoi_data)
                logger.info(f"✅ Auto-synced {len(ukeoi_data)} contract employees (Ukeoi)")
            else:
                logger.warning(f"⚠️ Employee registry not found at: {EMPLOYEE_REGISTRY_PATH}")
        else:
            logger.info(f"✅ Database already has {len(employees)} employees - skipping auto-sync")

    except Exception as e:
        logger.error(f"❌ Auto-sync failed: {str(e)}")
        # Don't raise - allow server to start even if sync fails

# ============================================
# STARTUP / SHUTDOWN EVENTS FOR CONNECTION POOL
# ============================================

@app.on_event("startup")
async def startup_event():
    """
    Initialization on application startup.
    - Validates production secrets configuration
    - Initializes database connection pool (for PostgreSQL)
    - Runs auto-sync if database is empty
    - Creates backup if database has data
    """
    try:
        logger.info("Starting up YuKyuDATA application...")

        # Validate secrets configuration (critical for production security)
        logger.info("Validating secrets configuration...")
        is_valid, errors, warnings = validate_secrets(exit_on_failure=True)

        if warnings:
            for warning in warnings:
                logger.warning(f"Security warning: {warning}")

        if is_valid:
            logger.info("Secrets validation passed")
        else:
            # In development mode, log errors but continue
            for error in errors:
                logger.error(f"Security error: {error}")

        # Initialize connection pool if using PostgreSQL
        if database.USE_POSTGRESQL:
            logger.info("🔌 Initializing PostgreSQL connection pool...")
            from database.connection import PostgreSQLConnectionPool
            database_url = os.getenv('DATABASE_URL')
            pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
            pool_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
            PostgreSQLConnectionPool.initialize(database_url, pool_size, pool_overflow)
            logger.info(f"✅ PostgreSQL pool initialized: {pool_size} min, {pool_overflow} max connections")
        else:
            logger.info("🗄️  Using SQLite database (no connection pool)")

        # Run auto-sync
        auto_sync_on_startup()

        logger.info("✅ Startup complete")
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown.
    - Closes all database connections in the pool
    """
    try:
        logger.info("🛑 Shutting down YuKyuDATA application...")

        if database.USE_POSTGRESQL:
            logger.info("🔌 Closing PostgreSQL connection pool...")
            from database.connection import PostgreSQLConnectionPool
            PostgreSQLConnectionPool.close_pool()
            logger.info("✅ Connection pool closed")

        logger.info("✅ Shutdown complete")
    except Exception as e:
        logger.error(f"⚠️  Shutdown error: {str(e)}", exc_info=True)

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
    logger.info("Starting YuKyuDATA-app server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# === END OF FILE ===
# The following code has been removed as it was duplicated in routes/
# See routes/ directory for all API endpoints
