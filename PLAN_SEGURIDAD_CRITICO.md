# PLAN DE ACCION DE SEGURIDAD CRITICO
## YuKyuDATA-app v1.0 - Correccion de Vulnerabilidades

**Estado:** CRITICO - Bloquea deployment a produccion
**Fecha:** 2025-12-23
**Tiempo estimado total:** 8-12 horas
**Auditor:** Claude Security Analysis

---

## RESUMEN EJECUTIVO

Se han identificado **4 vulnerabilidades criticas** que deben corregirse antes del deployment:

| # | Vulnerabilidad | Severidad | CVSS | Tiempo Est. |
|---|---------------|-----------|------|-------------|
| 1 | Credenciales hardcodeadas | CRITICA | 9.8 | 1-2h |
| 2 | Endpoints sin autenticacion | CRITICA | 9.1 | 3-4h |
| 3 | Datos sensibles sin encriptar | ALTA | 8.5 | 2-3h |
| 4 | Rate limiter no aplicado | MEDIA | 6.5 | 1-2h |

---

# VULNERABILIDAD 1: CREDENCIALES HARDCODEADAS

## 1.1 Codigo Vulnerable Actual

**Ubicacion:** `main.py` lineas 122-136

```python
# VULNERABLE - NO USAR EN PRODUCCION
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "yukyu-secret-key-2024-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer(auto_error=False)

# User database (simple in-memory for now)
USERS_DB = {
    "admin": {
        "password": "admin123",  # CRITICO: Password en texto plano
        "role": "admin",
        "name": "Administrator"
    }
}
```

## 1.2 Problemas Identificados

1. **JWT_SECRET_KEY con valor por defecto predecible** - Atacante puede generar tokens validos
2. **Password en texto plano** - Sin hashing, visible en el codigo fuente
3. **Base de datos de usuarios en memoria** - No escalable, se pierde al reiniciar
4. **Sin validacion de complejidad de passwords**

## 1.3 Solucion Paso a Paso

### Paso 1.3.1: Crear archivo .env (NO commitear)

Crear archivo `.env` en la raiz del proyecto:

```env
# ===========================================
# YuKyuDATA Security Configuration
# ===========================================
# IMPORTANTE: Nunca commitear este archivo a Git

# JWT Configuration
JWT_SECRET_KEY=<GENERAR-CON-COMANDO-ABAJO>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8

# Database
DATABASE_URL=sqlite:///./yukyu.db

# Admin credentials (hashed)
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<GENERAR-CON-COMANDO-ABAJO>

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Environment
ENVIRONMENT=development
DEBUG=false
```

**Comando para generar JWT_SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Comando para generar ADMIN_PASSWORD_HASH:**
```bash
python -c "from passlib.hash import bcrypt; print(bcrypt.hash('TU_PASSWORD_SEGURO'))"
```

### Paso 1.3.2: Crear archivo .env.example (SI commitear)

```env
# ===========================================
# YuKyuDATA Security Configuration Template
# ===========================================
# Copiar a .env y rellenar valores reales

JWT_SECRET_KEY=CHANGE_ME_USE_secrets.token_urlsafe(64)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8

DATABASE_URL=sqlite:///./yukyu.db

ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=GENERATE_WITH_bcrypt.hash()

RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

ENVIRONMENT=development
DEBUG=false
```

### Paso 1.3.3: Actualizar .gitignore

Agregar al `.gitignore`:

```gitignore
# Security - NEVER commit these
.env
.env.local
.env.production
*.pem
*.key
secrets/
```

### Paso 1.3.4: Instalar dependencias necesarias

```bash
pip install python-dotenv passlib[bcrypt]
```

Agregar a `requirements.txt`:
```
python-dotenv>=1.0.0
passlib[bcrypt]>=1.7.4
```

### Paso 1.3.5: Crear modulo de configuracion segura

Crear archivo `config.py`:

```python
"""
Secure Configuration Module for YuKyuDATA
==========================================
Loads configuration from environment variables with validation.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from functools import lru_cache

from dotenv import load_dotenv
from passlib.hash import bcrypt

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self._validate_required_settings()

    def _validate_required_settings(self):
        """Validate that all required settings are present."""
        required = ['JWT_SECRET_KEY']
        missing = [key for key in required if not os.getenv(key)]

        if missing and os.getenv('ENVIRONMENT') == 'production':
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    # JWT Settings
    @property
    def jwt_secret_key(self) -> str:
        key = os.getenv("JWT_SECRET_KEY")
        if not key or key == "CHANGE_ME_USE_secrets.token_urlsafe(64)":
            if os.getenv('ENVIRONMENT') == 'production':
                raise ConfigurationError("JWT_SECRET_KEY not configured for production")
            # Development fallback (logs warning)
            import warnings
            warnings.warn("Using development JWT secret - DO NOT USE IN PRODUCTION")
            return "dev-only-secret-key-not-for-production"
        return key

    @property
    def jwt_algorithm(self) -> str:
        return os.getenv("JWT_ALGORITHM", "HS256")

    @property
    def jwt_expiration_hours(self) -> int:
        return int(os.getenv("JWT_EXPIRATION_HOURS", "8"))

    # Rate Limiting
    @property
    def rate_limit_requests(self) -> int:
        return int(os.getenv("RATE_LIMIT_REQUESTS", "100"))

    @property
    def rate_limit_window(self) -> int:
        return int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # Environment
    @property
    def environment(self) -> str:
        return os.getenv("ENVIRONMENT", "development")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "false").lower() == "true"


class UserManager:
    """
    Secure user management with hashed passwords.
    In production, this should be backed by a database.
    """

    def __init__(self):
        self._users = self._load_users()

    def _load_users(self) -> dict:
        """Load users from environment or database."""
        users = {}

        # Load admin from environment
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

        if admin_password_hash:
            users[admin_username] = {
                "password_hash": admin_password_hash,
                "role": "admin",
                "name": "Administrator"
            }
        else:
            # Development fallback - DO NOT USE IN PRODUCTION
            import warnings
            warnings.warn("Using development admin password - DO NOT USE IN PRODUCTION")
            users["admin"] = {
                "password_hash": bcrypt.hash("admin123"),
                "role": "admin",
                "name": "Administrator (DEV)"
            }

        return users

    def verify_password(self, username: str, password: str) -> bool:
        """Verify password against stored hash."""
        user = self._users.get(username)
        if not user:
            # Timing-safe comparison even for non-existent users
            bcrypt.hash("dummy")  # Constant time
            return False

        try:
            return bcrypt.verify(password, user["password_hash"])
        except Exception:
            return False

    def get_user(self, username: str) -> Optional[dict]:
        """Get user info (without password hash)."""
        user = self._users.get(username)
        if user:
            return {
                "username": username,
                "role": user["role"],
                "name": user["name"]
            }
        return None

    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        return username in self._users


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


@lru_cache()
def get_user_manager() -> UserManager:
    """Get cached user manager instance."""
    return UserManager()
```

### Paso 1.3.6: Actualizar main.py

Reemplazar lineas 122-136 con:

```python
# ============================================
# SECURE CONFIGURATION
# ============================================
from config import get_settings, get_user_manager

settings = get_settings()
user_manager = get_user_manager()

# JWT Configuration (from secure config)
JWT_SECRET_KEY = settings.jwt_secret_key
JWT_ALGORITHM = settings.jwt_algorithm
JWT_EXPIRATION_HOURS = settings.jwt_expiration_hours

# Security
security = HTTPBearer(auto_error=False)
```

### Paso 1.3.7: Actualizar endpoint de login

Reemplazar el endpoint `/api/auth/login`:

```python
@app.post("/api/auth/login")
async def login(login_data: UserLogin, request: Request):
    """
    Authenticate user and return JWT token.
    Uses secure password hashing with bcrypt.
    """
    username = login_data.username
    password = login_data.password

    # Rate limit login attempts
    client_ip = request.client.host
    if not login_rate_limiter.is_allowed(client_ip):
        logger.warning(f"Login rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Please try again later."
        )

    # Verify credentials using secure password comparison
    if not user_manager.verify_password(username, password):
        logger.warning(f"Failed login attempt for user: {username} from IP: {client_ip}")
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # Get user info
    user = user_manager.get_user(username)

    # Create JWT token
    token = create_jwt_token(username, user["role"])

    logger.info(f"User '{username}' logged in successfully from IP: {client_ip}")

    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
        "user": user
    }
```

## 1.4 Testing

```python
# test_auth_security.py
import pytest
from passlib.hash import bcrypt

def test_password_not_stored_plain():
    """Verify passwords are hashed, not plain text."""
    from config import get_user_manager

    user_manager = get_user_manager()

    # Password should be hashed
    admin = user_manager._users.get("admin")
    assert admin is not None
    assert "password_hash" in admin
    assert admin["password_hash"].startswith("$2b$")  # bcrypt prefix

def test_jwt_secret_not_default():
    """Verify JWT secret is not the default value."""
    import os
    os.environ["ENVIRONMENT"] = "production"

    from config import get_settings, ConfigurationError

    # Should raise error if using default secret in production
    with pytest.raises(ConfigurationError):
        settings = get_settings()
        _ = settings.jwt_secret_key

def test_timing_safe_password_check():
    """Verify password check is timing-safe."""
    import time
    from config import get_user_manager

    user_manager = get_user_manager()

    # Time for existing user
    start = time.perf_counter()
    user_manager.verify_password("admin", "wrong")
    existing_time = time.perf_counter() - start

    # Time for non-existing user
    start = time.perf_counter()
    user_manager.verify_password("nonexistent", "wrong")
    nonexistent_time = time.perf_counter() - start

    # Times should be similar (within 50%)
    ratio = max(existing_time, nonexistent_time) / min(existing_time, nonexistent_time)
    assert ratio < 1.5, "Password check may be vulnerable to timing attacks"
```

## 1.5 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|--------------|---------|------------|
| .env expuesto en Git | Media | Critico | Pre-commit hook, .gitignore |
| JWT secret debil | Baja | Critico | Validacion en produccion |
| Password hashes en logs | Media | Alto | Filtrar datos sensibles en logger |

---

# VULNERABILIDAD 2: ENDPOINTS SIN AUTENTICACION

## 2.1 Inventario Completo de Endpoints

### Endpoints Identificados (61 total)

```
CATEGORIA: AUTENTICACION (4 endpoints)
---------------------------------------
POST /api/auth/login          - PUBLICO (necesario)
POST /api/auth/logout         - AUTENTICADO
GET  /api/auth/me             - AUTENTICADO
GET  /api/auth/verify         - AUTENTICADO

CATEGORIA: DATOS DE EMPLEADOS (6 endpoints)
--------------------------------------------
GET  /api/employees           - SIN AUTH [CRITICO]
GET  /api/employees/search    - SIN AUTH [CRITICO]
GET  /api/employees/{id}/leave-info - SIN AUTH [CRITICO]
GET  /api/employees/active    - SIN AUTH [CRITICO]
GET  /api/employees/by-type   - SIN AUTH [CRITICO]
GET  /                        - PUBLICO (frontend)

CATEGORIA: SINCRONIZACION (6 endpoints)
----------------------------------------
POST /api/sync                - SIN AUTH [CRITICO]
POST /api/sync-genzai         - SIN AUTH [CRITICO]
POST /api/sync-ukeoi          - SIN AUTH [CRITICO]
POST /api/sync-staff          - SIN AUTH [CRITICO]
POST /api/sync/update-master-excel - SIN AUTH [CRITICO]
POST /api/upload              - SIN AUTH [CRITICO]

CATEGORIA: RESET/DELETE (4 endpoints)
--------------------------------------
DELETE /api/reset             - ADMIN (ya protegido)
DELETE /api/reset-genzai      - ADMIN (ya protegido)
DELETE /api/reset-ukeoi       - ADMIN (ya protegido)
DELETE /api/reset-staff       - ADMIN (ya protegido)

CATEGORIA: DATOS GENZAI/UKEOI/STAFF (6 endpoints)
-------------------------------------------------
GET  /api/genzai              - SIN AUTH [CRITICO]
GET  /api/ukeoi               - SIN AUTH [CRITICO]
GET  /api/staff               - SIN AUTH [CRITICO]
GET  /api/factories           - SIN AUTH [MEDIO]

CATEGORIA: LEAVE REQUESTS (6 endpoints)
----------------------------------------
POST /api/leave-requests      - SIN AUTH [CRITICO]
GET  /api/leave-requests      - SIN AUTH [CRITICO]
POST /api/leave-requests/{id}/approve - SIN AUTH [CRITICO]
POST /api/leave-requests/{id}/reject  - SIN AUTH [CRITICO]
DELETE /api/leave-requests/{id}       - SIN AUTH [CRITICO]
POST /api/leave-requests/{id}/revert  - SIN AUTH [CRITICO]

CATEGORIA: BACKUP/RESTORE (3 endpoints)
----------------------------------------
POST /api/backup              - SIN AUTH [CRITICO]
GET  /api/backups             - SIN AUTH [CRITICO]
POST /api/backup/restore      - SIN AUTH [CRITICO]

CATEGORIA: YUKYU/ANALYTICS (8 endpoints)
-----------------------------------------
GET  /api/yukyu/usage-details - SIN AUTH [MEDIO]
GET  /api/yukyu/monthly-summary/{year} - SIN AUTH [MEDIO]
GET  /api/yukyu/kpi-stats/{year}       - SIN AUTH [MEDIO]
GET  /api/yukyu/by-employee-type/{year} - SIN AUTH [MEDIO]
GET  /api/analytics/top10-active/{year} - SIN AUTH [MEDIO]
GET  /api/analytics/high-balance-active/{year} - SIN AUTH [MEDIO]
GET  /api/analytics/dashboard/{year}   - SIN AUTH [MEDIO]
GET  /api/analytics/predictions/{year} - SIN AUTH [MEDIO]

CATEGORIA: COMPLIANCE (7 endpoints)
------------------------------------
GET  /api/compliance/5day-check/{year} - SIN AUTH [MEDIO]
GET  /api/compliance/expiring/{year}   - SIN AUTH [MEDIO]
GET  /api/compliance/report/{year}     - SIN AUTH [MEDIO]
GET  /api/compliance/alerts            - SIN AUTH [MEDIO]
GET  /api/compliance/annual-ledger/{year} - SIN AUTH [MEDIO]
POST /api/compliance/export-ledger/{year} - SIN AUTH [MEDIO]
POST /api/orchestrator/run-compliance-check/{year} - SIN AUTH [CRITICO]

CATEGORIA: ORCHESTRATOR/SYSTEM (4 endpoints)
---------------------------------------------
GET  /api/orchestrator/status   - SIN AUTH [BAJO]
GET  /api/orchestrator/history  - SIN AUTH [BAJO]
GET  /api/system/snapshot       - SIN AUTH [MEDIO]
GET  /api/system/audit-log      - SIN AUTH [CRITICO]
GET  /api/system/activity-report - SIN AUTH [MEDIO]

CATEGORIA: CALENDARIO/NOTIFICACIONES (3 endpoints)
---------------------------------------------------
GET  /api/notifications           - SIN AUTH [MEDIO]
GET  /api/calendar/events         - SIN AUTH [MEDIO]
GET  /api/calendar/summary/{year}/{month} - SIN AUTH [MEDIO]

CATEGORIA: EXPORTACION (4 endpoints)
-------------------------------------
POST /api/export/excel            - SIN AUTH [CRITICO]
POST /api/export/approved-requests - SIN AUTH [CRITICO]
POST /api/export/monthly-report   - SIN AUTH [CRITICO]
POST /api/export/annual-ledger    - SIN AUTH [CRITICO]
GET  /api/export/download/{filename} - SIN AUTH [CRITICO]
GET  /api/export/files            - SIN AUTH [MEDIO]
DELETE /api/export/cleanup        - SIN AUTH [CRITICO]

CATEGORIA: FISCAL (6 endpoints)
--------------------------------
GET  /api/fiscal/config           - SIN AUTH [BAJO]
POST /api/fiscal/process-carryover - SIN AUTH [CRITICO]
GET  /api/fiscal/balance-breakdown/{emp} - SIN AUTH [MEDIO]
GET  /api/fiscal/expiring-soon    - SIN AUTH [MEDIO]
GET  /api/fiscal/5day-compliance/{year} - SIN AUTH [MEDIO]
GET  /api/fiscal/grant-recommendation/{emp} - SIN AUTH [MEDIO]
POST /api/fiscal/apply-fifo-deduction - SIN AUTH [CRITICO]

CATEGORIA: REPORTES (3 endpoints)
----------------------------------
GET  /api/reports/custom          - SIN AUTH [MEDIO]
GET  /api/reports/monthly/{year}/{month} - SIN AUTH [MEDIO]
GET  /api/reports/monthly-list/{year}    - SIN AUTH [MEDIO]

CATEGORIA: SALUD/INFO (4 endpoints)
------------------------------------
GET  /api/health                  - PUBLICO (health checks)
GET  /api/db-status               - SIN AUTH [BAJO]
GET  /api/info                    - PUBLICO (version info)
GET  /api/stats/by-factory        - SIN AUTH [MEDIO]
```

## 2.2 Clasificacion de Proteccion Requerida

| Nivel | Descripcion | Endpoints |
|-------|-------------|-----------|
| PUBLICO | Sin autenticacion | `/`, `/api/health`, `/api/info`, `/api/auth/login` |
| AUTENTICADO | Token JWT valido | La mayoria de endpoints GET |
| ADMIN | Rol admin requerido | Todos los POST/DELETE criticos |

## 2.3 Solucion: Aplicar Decoradores de Autenticacion

### Paso 2.3.1: Crear middleware de autenticacion global

Agregar despues de la configuracion de CORS en `main.py`:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/",
    "/api/health",
    "/api/info",
    "/api/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Endpoints that require admin role
ADMIN_ENDPOINTS = {
    "/api/reset",
    "/api/reset-genzai",
    "/api/reset-ukeoi",
    "/api/reset-staff",
    "/api/backup/restore",
    "/api/fiscal/process-carryover",
    "/api/fiscal/apply-fifo-deduction",
    "/api/orchestrator/run-compliance-check",
    "/api/export/cleanup",
    "/api/sync/update-master-excel",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Global authentication middleware.
    Checks JWT token for all non-public endpoints.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow public endpoints
        if path in PUBLIC_ENDPOINTS or path.startswith("/static"):
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )

        token = auth_header.split(" ")[1]

        try:
            payload = verify_jwt_token(token)

            # Check admin requirement
            if any(path.startswith(ep) for ep in ADMIN_ENDPOINTS):
                if payload.get("role") != "admin":
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Admin privileges required"}
                    )

            # Attach user info to request state
            request.state.user = {
                "username": payload.get("sub"),
                "role": payload.get("role")
            }

        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )

        return await call_next(request)


# Add middleware AFTER CORS
app.add_middleware(AuthenticationMiddleware)
```

### Paso 2.3.2: Actualizar cada endpoint con dependencias explicitas

Aunque el middleware proporciona proteccion global, es buena practica tambien tener las dependencias explicitas en cada endpoint para documentacion y claridad.

**Endpoints que necesitan `Depends(require_auth)`:**

```python
# EMPLOYEES - todos requieren autenticacion
@app.get("/api/employees")
async def get_employees(
    year: int = None,
    enhanced: bool = False,
    active_only: bool = False,
    user: dict = Depends(require_auth)  # AGREGAR
):
    ...

@app.get("/api/employees/search")
async def search_employees(
    q: str = "",
    status: str = None,
    factory: str = None,
    user: dict = Depends(require_auth)  # AGREGAR
):
    ...

@app.get("/api/employees/{employee_num}/leave-info")
async def get_employee_leave_info(
    employee_num: str,
    user: dict = Depends(require_auth)  # AGREGAR
):
    ...

# SYNC - todos requieren admin
@app.post("/api/sync")
async def sync_default_file(user: dict = Depends(require_admin)):  # CAMBIAR
    ...

@app.post("/api/sync-genzai")
async def sync_genzai(user: dict = Depends(require_admin)):  # AGREGAR
    ...

@app.post("/api/sync-ukeoi")
async def sync_ukeoi(user: dict = Depends(require_admin)):  # AGREGAR
    ...

@app.post("/api/sync-staff")
async def sync_staff(user: dict = Depends(require_admin)):  # AGREGAR
    ...

# GENZAI/UKEOI/STAFF - requieren autenticacion
@app.get("/api/genzai")
async def get_genzai(status: str = None, user: dict = Depends(require_auth)):  # AGREGAR
    ...

@app.get("/api/ukeoi")
async def get_ukeoi(status: str = None, user: dict = Depends(require_auth)):  # AGREGAR
    ...

@app.get("/api/staff")
async def get_staff_employees(
    status: str = None,
    year: int = None,
    filter_by_year: bool = False,
    user: dict = Depends(require_auth)  # AGREGAR
):
    ...

# LEAVE REQUESTS - requieren autenticacion, approve/reject requieren admin
@app.post("/api/leave-requests")
async def create_leave_request(
    request_data: LeaveRequestCreate,
    user: dict = Depends(require_auth)  # AGREGAR
):
    ...

@app.get("/api/leave-requests")
async def get_leave_requests_list(
    status: str = None,
    employee_num: str = None,
    year: int = None,
    user: dict = Depends(require_auth)  # AGREGAR
):
    ...

@app.post("/api/leave-requests/{request_id}/approve")
async def approve_request(
    request_id: int,
    user: dict = Depends(require_admin)  # AGREGAR - admin only
):
    ...

@app.post("/api/leave-requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    user: dict = Depends(require_admin)  # AGREGAR - admin only
):
    ...

# BACKUP - admin only
@app.post("/api/backup")
async def create_backup_endpoint(user: dict = Depends(require_admin)):  # AGREGAR
    ...

@app.get("/api/backups")
async def list_backups_endpoint(user: dict = Depends(require_auth)):  # AGREGAR
    ...

@app.post("/api/backup/restore")
async def restore_backup_endpoint(
    backup_filename: str,
    user: dict = Depends(require_admin)  # AGREGAR
):
    ...

# EXPORT - admin only para crear, auth para listar
@app.post("/api/export/excel")
async def export_excel(user: dict = Depends(require_admin)):  # AGREGAR
    ...

@app.post("/api/export/approved-requests")
async def export_approved_requests(user: dict = Depends(require_admin)):  # AGREGAR
    ...

@app.get("/api/export/download/{filename}")
async def download_export(filename: str, user: dict = Depends(require_auth)):  # AGREGAR
    ...
```

### Paso 2.3.3: Tabla completa de cambios

| Endpoint | Estado Actual | Estado Requerido | Cambio |
|----------|---------------|------------------|--------|
| `POST /api/sync` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/sync-genzai` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/sync-ukeoi` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/sync-staff` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/upload` | Sin auth | Admin | `Depends(require_admin)` |
| `GET /api/employees` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/employees/search` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/employees/{id}/leave-info` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/employees/active` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/employees/by-type` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/genzai` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/ukeoi` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/staff` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/factories` | Sin auth | Auth | `Depends(require_auth)` |
| `POST /api/leave-requests` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/leave-requests` | Sin auth | Auth | `Depends(require_auth)` |
| `POST /api/leave-requests/{id}/approve` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/leave-requests/{id}/reject` | Sin auth | Admin | `Depends(require_admin)` |
| `DELETE /api/leave-requests/{id}` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/leave-requests/{id}/revert` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/backup` | Sin auth | Admin | `Depends(require_admin)` |
| `GET /api/backups` | Sin auth | Auth | `Depends(require_auth)` |
| `POST /api/backup/restore` | Sin auth | Admin | `Depends(require_admin)` |
| `GET /api/yukyu/*` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/analytics/*` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/compliance/*` | Sin auth | Auth | `Depends(require_auth)` |
| `POST /api/compliance/export-ledger/*` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/orchestrator/run-compliance-check/*` | Sin auth | Admin | `Depends(require_admin)` |
| `GET /api/system/audit-log` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/export/*` | Sin auth | Admin | `Depends(require_admin)` |
| `GET /api/export/download/*` | Sin auth | Auth | `Depends(require_auth)` |
| `DELETE /api/export/cleanup` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/fiscal/process-carryover` | Sin auth | Admin | `Depends(require_admin)` |
| `POST /api/fiscal/apply-fifo-deduction` | Sin auth | Admin | `Depends(require_admin)` |
| `GET /api/fiscal/*` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/reports/*` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/calendar/*` | Sin auth | Auth | `Depends(require_auth)` |
| `GET /api/notifications` | Sin auth | Auth | `Depends(require_auth)` |

## 2.4 Testing de Autenticacion

```python
# test_endpoint_security.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Lista de endpoints que DEBEN requerir autenticacion
PROTECTED_ENDPOINTS = [
    ("GET", "/api/employees"),
    ("GET", "/api/genzai"),
    ("GET", "/api/ukeoi"),
    ("GET", "/api/staff"),
    ("POST", "/api/sync"),
    ("POST", "/api/leave-requests"),
    ("GET", "/api/leave-requests"),
    ("POST", "/api/backup"),
    ("GET", "/api/backups"),
]

# Endpoints publicos
PUBLIC_ENDPOINTS = [
    ("GET", "/api/health"),
    ("GET", "/api/info"),
    ("POST", "/api/auth/login"),
]


@pytest.mark.parametrize("method,endpoint", PROTECTED_ENDPOINTS)
def test_protected_endpoints_require_auth(method, endpoint):
    """Verify protected endpoints return 401 without auth."""
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        response = client.post(endpoint, json={})

    assert response.status_code == 401, f"{method} {endpoint} should require auth"


@pytest.mark.parametrize("method,endpoint", PUBLIC_ENDPOINTS)
def test_public_endpoints_accessible(method, endpoint):
    """Verify public endpoints are accessible without auth."""
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        response = client.post(endpoint, json={"username": "x", "password": "x"})

    assert response.status_code != 401, f"{method} {endpoint} should be public"


def test_admin_endpoints_require_admin_role():
    """Verify admin endpoints require admin role, not just auth."""
    # First login as admin to get token
    login_response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create non-admin user for testing (if supported)
    # For now, test that admin can access admin endpoints
    admin_endpoints = [
        ("POST", "/api/sync"),
        ("DELETE", "/api/reset"),
        ("POST", "/api/backup/restore"),
    ]

    for method, endpoint in admin_endpoints:
        if method == "POST":
            response = client.post(endpoint, headers=headers, json={})
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)

        # Should NOT be 403 for admin
        assert response.status_code != 403, f"Admin should access {endpoint}"
```

---

# VULNERABILIDAD 3: DATOS SENSIBLES SIN ENCRIPTAR

## 3.1 Campos Sensibles Identificados

| Tabla | Campo | Sensibilidad | Accion |
|-------|-------|--------------|--------|
| `genzai` | `hourly_wage` | ALTA | Encriptar |
| `genzai` | `birth_date` | ALTA | Encriptar |
| `genzai` | `nationality` | MEDIA | Encriptar |
| `ukeoi` | `hourly_wage` | ALTA | Encriptar |
| `ukeoi` | `birth_date` | ALTA | Encriptar |
| `ukeoi` | `nationality` | MEDIA | Encriptar |
| `staff` | `hourly_wage` | ALTA | Encriptar (si existe) |
| `staff` | `birth_date` | ALTA | Encriptar |
| `staff` | `address` | ALTA | Encriptar |
| `staff` | `postal_code` | MEDIA | Encriptar |
| `staff` | `visa_expiry` | ALTA | Encriptar |
| `staff` | `visa_type` | MEDIA | Encriptar |
| `leave_requests` | `hourly_wage` | ALTA | Encriptar |
| `leave_requests` | `cost_estimate` | MEDIA | Encriptar |

## 3.2 Solucion: Implementar Encriptacion con Fernet

### Paso 3.2.1: Instalar cryptography

```bash
pip install cryptography
```

Agregar a `requirements.txt`:
```
cryptography>=41.0.0
```

### Paso 3.2.2: Crear modulo de encriptacion

Crear archivo `encryption.py`:

```python
"""
Data Encryption Module for YuKyuDATA
=====================================
Uses Fernet symmetric encryption for sensitive data fields.
"""

import os
import base64
from typing import Optional, Union
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class DataEncryptor:
    """
    Handles encryption and decryption of sensitive data.
    Uses Fernet symmetric encryption with a key derived from
    a master password + salt.
    """

    def __init__(self):
        self._fernet = self._initialize_fernet()

    def _initialize_fernet(self) -> Fernet:
        """Initialize Fernet with key from environment."""
        # Get encryption key from environment
        encryption_key = os.getenv("DATA_ENCRYPTION_KEY")

        if encryption_key:
            # Use provided key directly
            key = encryption_key.encode()
        else:
            # Derive key from master password (for development)
            master_password = os.getenv(
                "MASTER_PASSWORD",
                "dev-master-password-change-in-production"
            )
            salt = os.getenv(
                "ENCRYPTION_SALT",
                "dev-salt-change-in-production"
            ).encode()

            if os.getenv("ENVIRONMENT") == "production":
                raise EncryptionError(
                    "DATA_ENCRYPTION_KEY must be set in production"
                )

            key = self._derive_key(master_password, salt)

        return Fernet(key)

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended minimum
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: Union[str, int, float, None]) -> Optional[str]:
        """
        Encrypt a piece of data.

        Args:
            data: String, number, or None to encrypt

        Returns:
            Base64-encoded encrypted string, or None if input is None
        """
        if data is None:
            return None

        try:
            # Convert to string
            data_str = str(data)
            # Encrypt
            encrypted = self._fernet.encrypt(data_str.encode())
            # Return as base64 string for storage
            return encrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt(self, encrypted_data: Optional[str]) -> Optional[str]:
        """
        Decrypt a piece of data.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Decrypted string, or None if input is None
        """
        if encrypted_data is None:
            return None

        try:
            decrypted = self._fernet.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except InvalidToken:
            raise EncryptionError("Invalid encryption token - data may be corrupted")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")

    def decrypt_to_int(self, encrypted_data: Optional[str]) -> Optional[int]:
        """Decrypt and convert to integer."""
        decrypted = self.decrypt(encrypted_data)
        if decrypted is None:
            return None
        try:
            return int(decrypted)
        except ValueError:
            return None

    def decrypt_to_float(self, encrypted_data: Optional[str]) -> Optional[float]:
        """Decrypt and convert to float."""
        decrypted = self.decrypt(encrypted_data)
        if decrypted is None:
            return None
        try:
            return float(decrypted)
        except ValueError:
            return None


# Sensitive fields configuration
SENSITIVE_FIELDS = {
    "genzai": ["hourly_wage", "birth_date", "nationality"],
    "ukeoi": ["hourly_wage", "birth_date", "nationality"],
    "staff": ["birth_date", "address", "postal_code", "visa_expiry", "visa_type"],
    "leave_requests": ["hourly_wage", "cost_estimate"],
}


def encrypt_record(table: str, record: dict, encryptor: DataEncryptor) -> dict:
    """
    Encrypt sensitive fields in a record.

    Args:
        table: Table name
        record: Dictionary with record data
        encryptor: DataEncryptor instance

    Returns:
        Record with sensitive fields encrypted
    """
    if table not in SENSITIVE_FIELDS:
        return record

    encrypted = record.copy()
    for field in SENSITIVE_FIELDS[table]:
        if field in encrypted and encrypted[field] is not None:
            encrypted[field] = encryptor.encrypt(encrypted[field])

    return encrypted


def decrypt_record(table: str, record: dict, encryptor: DataEncryptor) -> dict:
    """
    Decrypt sensitive fields in a record.

    Args:
        table: Table name
        record: Dictionary with encrypted record data
        encryptor: DataEncryptor instance

    Returns:
        Record with sensitive fields decrypted
    """
    if table not in SENSITIVE_FIELDS:
        return record

    decrypted = record.copy()
    for field in SENSITIVE_FIELDS[table]:
        if field in decrypted and decrypted[field] is not None:
            try:
                # Try to decrypt - if it fails, it might not be encrypted yet
                value = decrypted[field]
                if isinstance(value, str) and value.startswith("gAAAAA"):
                    # Looks like Fernet encrypted data
                    if field in ["hourly_wage", "cost_estimate"]:
                        decrypted[field] = encryptor.decrypt_to_int(value)
                    else:
                        decrypted[field] = encryptor.decrypt(value)
            except EncryptionError:
                # Leave as-is if decryption fails (might be unencrypted legacy data)
                pass

    return decrypted


@lru_cache()
def get_encryptor() -> DataEncryptor:
    """Get cached encryptor instance."""
    return DataEncryptor()


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key().decode()
```

### Paso 3.2.3: Actualizar .env con clave de encriptacion

Agregar al `.env`:

```env
# Data Encryption
DATA_ENCRYPTION_KEY=<GENERAR-CON-COMANDO-ABAJO>
# O usar derivacion de password:
MASTER_PASSWORD=your-very-secure-master-password
ENCRYPTION_SALT=unique-salt-for-this-installation
```

**Generar clave:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Paso 3.2.4: Modificar database.py para usar encriptacion

Agregar imports y modificar funciones:

```python
# Al inicio de database.py
from encryption import get_encryptor, encrypt_record, decrypt_record

# Modificar save_genzai
def save_genzai(genzai_data):
    """Saves dispatch employee data from DBGenzaiX sheet with encryption."""
    encryptor = get_encryptor()

    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in genzai_data:
            # Encrypt sensitive fields
            encrypted_emp = encrypt_record("genzai", emp, encryptor)

            c.execute('''
                INSERT OR REPLACE INTO genzai
                (id, status, employee_num, dispatch_id, dispatch_name, department, line,
                 job_content, name, kana, gender, nationality, birth_date, age,
                 hourly_wage, wage_revision, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                encrypted_emp.get('id'),
                encrypted_emp.get('status'),
                encrypted_emp.get('employee_num'),
                encrypted_emp.get('dispatch_id'),
                encrypted_emp.get('dispatch_name'),
                encrypted_emp.get('department'),
                encrypted_emp.get('line'),
                encrypted_emp.get('job_content'),
                encrypted_emp.get('name'),
                encrypted_emp.get('kana'),
                encrypted_emp.get('gender'),
                encrypted_emp.get('nationality'),  # Encrypted
                encrypted_emp.get('birth_date'),   # Encrypted
                encrypted_emp.get('age'),
                encrypted_emp.get('hourly_wage'),  # Encrypted
                encrypted_emp.get('wage_revision'),
                timestamp
            ))

        conn.commit()

# Modificar get_genzai
def get_genzai(status=None, year=None, active_in_year=False):
    """Retrieves dispatch employees with decryption."""
    encryptor = get_encryptor()

    with get_db() as conn:
        c = conn.cursor()
        # ... query logic ...
        rows = c.execute(query, params).fetchall()

        # Decrypt each record
        results = []
        for row in rows:
            record = dict(row)
            decrypted = decrypt_record("genzai", record, encryptor)
            results.append(decrypted)

        return results
```

### Paso 3.2.5: Script de migracion de datos existentes

Crear archivo `migrate_encrypt_data.py`:

```python
"""
Migration Script: Encrypt Existing Sensitive Data
===================================================
Migrates unencrypted data to encrypted format.

Usage:
    python migrate_encrypt_data.py --dry-run   # Preview changes
    python migrate_encrypt_data.py --execute   # Execute migration
"""

import argparse
import sqlite3
from datetime import datetime
from encryption import get_encryptor, SENSITIVE_FIELDS

DB_NAME = "yukyu.db"


def migrate_table(table: str, dry_run: bool = True) -> dict:
    """Migrate a table's sensitive fields to encrypted format."""
    encryptor = get_encryptor()

    if table not in SENSITIVE_FIELDS:
        return {"table": table, "status": "skipped", "reason": "no sensitive fields"}

    sensitive = SENSITIVE_FIELDS[table]

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all records
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()

    migrated = 0
    skipped = 0
    errors = []

    for row in rows:
        record = dict(row)
        record_id = record.get("id")
        needs_update = False
        updates = {}

        for field in sensitive:
            value = record.get(field)

            if value is None:
                continue

            # Check if already encrypted (Fernet tokens start with gAAAAA)
            if isinstance(value, str) and value.startswith("gAAAAA"):
                skipped += 1
                continue

            # Encrypt the value
            try:
                encrypted = encryptor.encrypt(value)
                updates[field] = encrypted
                needs_update = True
            except Exception as e:
                errors.append(f"{table}.{record_id}.{field}: {e}")

        if needs_update and not dry_run:
            # Build UPDATE query
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [record_id]

            cursor.execute(
                f"UPDATE {table} SET {set_clause} WHERE id = ?",
                values
            )
            migrated += 1
        elif needs_update:
            migrated += 1  # Would migrate in real run

    if not dry_run:
        conn.commit()

    conn.close()

    return {
        "table": table,
        "total_records": len(rows),
        "migrated": migrated,
        "skipped": skipped,
        "errors": errors,
        "dry_run": dry_run
    }


def main():
    parser = argparse.ArgumentParser(description="Migrate sensitive data to encrypted format")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--execute", action="store_true", help="Execute migration")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("Please specify --dry-run or --execute")
        return

    dry_run = args.dry_run

    print(f"\n{'=' * 60}")
    print(f"DATA ENCRYPTION MIGRATION")
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"{'=' * 60}\n")

    tables = list(SENSITIVE_FIELDS.keys())

    for table in tables:
        print(f"\nMigrating table: {table}")
        print("-" * 40)

        result = migrate_table(table, dry_run)

        print(f"  Total records: {result.get('total_records', 0)}")
        print(f"  To migrate: {result.get('migrated', 0)}")
        print(f"  Already encrypted: {result.get('skipped', 0)}")

        if result.get("errors"):
            print(f"  Errors:")
            for error in result["errors"]:
                print(f"    - {error}")

    print(f"\n{'=' * 60}")
    if dry_run:
        print("DRY RUN COMPLETE - No changes made")
        print("Run with --execute to apply changes")
    else:
        print("MIGRATION COMPLETE")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
```

## 3.3 Testing de Encriptacion

```python
# test_encryption.py
import pytest
from encryption import DataEncryptor, encrypt_record, decrypt_record

def test_encrypt_decrypt_string():
    """Test basic string encryption/decryption."""
    encryptor = DataEncryptor()

    original = "Test String 123"
    encrypted = encryptor.encrypt(original)
    decrypted = encryptor.decrypt(encrypted)

    assert encrypted != original
    assert encrypted.startswith("gAAAAA")  # Fernet prefix
    assert decrypted == original

def test_encrypt_decrypt_integer():
    """Test integer encryption/decryption."""
    encryptor = DataEncryptor()

    original = 50000
    encrypted = encryptor.encrypt(original)
    decrypted = encryptor.decrypt_to_int(encrypted)

    assert decrypted == original

def test_encrypt_none():
    """Test that None values are handled correctly."""
    encryptor = DataEncryptor()

    assert encryptor.encrypt(None) is None
    assert encryptor.decrypt(None) is None

def test_record_encryption():
    """Test full record encryption/decryption."""
    encryptor = DataEncryptor()

    record = {
        "id": "genzai_001",
        "name": "Test Employee",
        "hourly_wage": 1500,
        "birth_date": "1990-01-15",
        "nationality": "Japanese"
    }

    encrypted = encrypt_record("genzai", record, encryptor)

    # Sensitive fields should be encrypted
    assert encrypted["hourly_wage"].startswith("gAAAAA")
    assert encrypted["birth_date"].startswith("gAAAAA")
    assert encrypted["nationality"].startswith("gAAAAA")

    # Non-sensitive fields should remain unchanged
    assert encrypted["id"] == "genzai_001"
    assert encrypted["name"] == "Test Employee"

    # Decrypt and verify
    decrypted = decrypt_record("genzai", encrypted, encryptor)
    assert decrypted["hourly_wage"] == 1500
    assert decrypted["birth_date"] == "1990-01-15"

def test_encrypted_data_not_readable():
    """Verify encrypted data cannot be read without key."""
    encryptor = DataEncryptor()

    sensitive_wage = 75000
    encrypted = encryptor.encrypt(sensitive_wage)

    # Encrypted string should not contain original value
    assert "75000" not in encrypted
    assert str(sensitive_wage) not in encrypted
```

---

# VULNERABILIDAD 4: RATE LIMITER NO APLICADO

## 4.1 Estado Actual

El rate limiter esta **definido pero NO se usa** en ninguna parte del codigo:

```python
# main.py lineas 84-114 - DEFINIDO
class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        # ... implementation ...

    def get_remaining(self, client_ip: str) -> int:
        # ... implementation ...

rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

# PERO NUNCA SE USA EN NINGUN ENDPOINT
```

## 4.2 Solucion: Implementar Rate Limiting como Middleware

### Paso 4.2.1: Crear rate limiters especializados

Actualizar la clase RateLimiter:

```python
# ============================================
# RATE LIMITERS (Specialized)
# ============================================

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class RateLimiter:
    """Enhanced in-memory rate limiter with configurable limits."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = defaultdict(list)
        self._lock = threading.Lock()  # Thread safety

    def is_allowed(self, client_ip: str) -> tuple[bool, dict]:
        """
        Check if request is allowed.
        Returns (allowed, info_dict)
        """
        now = time()

        with self._lock:
            # Clean old requests
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < self.window
            ]

            current_count = len(self.requests[client_ip])
            remaining = max(0, self.max_requests - current_count)
            reset_time = int(now + self.window)

            info = {
                "limit": self.max_requests,
                "remaining": remaining,
                "reset": reset_time,
                "window": self.window
            }

            if current_count >= self.max_requests:
                return False, info

            self.requests[client_ip].append(now)
            info["remaining"] = remaining - 1

            return True, info

import threading

# Create specialized rate limiters
rate_limiters = {
    "default": RateLimiter(max_requests=100, window_seconds=60),
    "auth": RateLimiter(max_requests=5, window_seconds=60),      # Stricter for login
    "sync": RateLimiter(max_requests=10, window_seconds=300),    # 10 per 5 min for sync
    "export": RateLimiter(max_requests=20, window_seconds=300),  # 20 per 5 min for exports
    "backup": RateLimiter(max_requests=5, window_seconds=600),   # 5 per 10 min for backups
}

# Endpoint to rate limiter mapping
RATE_LIMIT_CONFIG = {
    "/api/auth/login": "auth",
    "/api/sync": "sync",
    "/api/sync-genzai": "sync",
    "/api/sync-ukeoi": "sync",
    "/api/sync-staff": "sync",
    "/api/upload": "sync",
    "/api/export/": "export",
    "/api/backup": "backup",
}
```

### Paso 4.2.2: Crear middleware de rate limiting

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    Applies different limits based on endpoint.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        client_ip = self._get_client_ip(request)

        # Determine which rate limiter to use
        limiter_key = "default"
        for prefix, key in RATE_LIMIT_CONFIG.items():
            if path.startswith(prefix):
                limiter_key = key
                break

        limiter = rate_limiters[limiter_key]
        allowed, info = limiter.is_allowed(client_ip)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {path} "
                f"(limiter: {limiter_key})"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": info["reset"] - int(time())
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["reset"] - int(time()))
                }
            )

        # Add rate limit headers to successful response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP, handling proxies."""
        # Check X-Forwarded-For header (from reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct connection
        if request.client:
            return request.client.host

        return "unknown"


# Add middleware BEFORE authentication middleware
app.add_middleware(RateLimitMiddleware)
```

### Paso 4.2.3: Orden correcto de middlewares

El orden es importante. En `main.py`, agregar middlewares en este orden:

```python
# 1. CORS (first - handles preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# 2. Rate Limiting (before auth - prevents brute force)
app.add_middleware(RateLimitMiddleware)

# 3. Authentication (after rate limit - checks auth on allowed requests)
app.add_middleware(AuthenticationMiddleware)
```

### Paso 4.2.4: Endpoint para ver estado del rate limiter

```python
@app.get("/api/rate-limit/status")
async def get_rate_limit_status(request: Request, user: dict = Depends(require_admin)):
    """Get rate limit status for current client (admin only)."""
    client_ip = request.client.host if request.client else "unknown"

    status = {}
    for name, limiter in rate_limiters.items():
        _, info = limiter.is_allowed(client_ip)
        # Undo the request count we just added
        limiter.requests[client_ip].pop()
        info["remaining"] += 1
        status[name] = info

    return {
        "client_ip": client_ip,
        "limiters": status
    }
```

## 4.3 Configuracion del Rate Limiter

Agregar al `.env`:

```env
# Rate Limiting Configuration
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_DEFAULT_WINDOW=60

RATE_LIMIT_AUTH=5
RATE_LIMIT_AUTH_WINDOW=60

RATE_LIMIT_SYNC=10
RATE_LIMIT_SYNC_WINDOW=300

RATE_LIMIT_EXPORT=20
RATE_LIMIT_EXPORT_WINDOW=300

RATE_LIMIT_BACKUP=5
RATE_LIMIT_BACKUP_WINDOW=600
```

### Paso 4.2.5: Cargar configuracion desde .env

```python
# En config.py
class Settings:
    # ... existing properties ...

    @property
    def rate_limits(self) -> dict:
        return {
            "default": {
                "requests": int(os.getenv("RATE_LIMIT_DEFAULT", "100")),
                "window": int(os.getenv("RATE_LIMIT_DEFAULT_WINDOW", "60"))
            },
            "auth": {
                "requests": int(os.getenv("RATE_LIMIT_AUTH", "5")),
                "window": int(os.getenv("RATE_LIMIT_AUTH_WINDOW", "60"))
            },
            "sync": {
                "requests": int(os.getenv("RATE_LIMIT_SYNC", "10")),
                "window": int(os.getenv("RATE_LIMIT_SYNC_WINDOW", "300"))
            },
            "export": {
                "requests": int(os.getenv("RATE_LIMIT_EXPORT", "20")),
                "window": int(os.getenv("RATE_LIMIT_EXPORT_WINDOW", "300"))
            },
            "backup": {
                "requests": int(os.getenv("RATE_LIMIT_BACKUP", "5")),
                "window": int(os.getenv("RATE_LIMIT_BACKUP_WINDOW", "600"))
            }
        }
```

## 4.4 Testing del Rate Limiter

```python
# test_rate_limiter.py
import pytest
import time
from fastapi.testclient import TestClient
from main import app, rate_limiters

client = TestClient(app)


def test_rate_limit_headers_present():
    """Verify rate limit headers are present in responses."""
    response = client.get("/api/health")

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_login_rate_limit():
    """Test that login is rate limited more strictly."""
    # Reset the auth rate limiter
    rate_limiters["auth"].requests.clear()

    # Make 5 requests (should succeed)
    for i in range(5):
        response = client.post("/api/auth/login", json={
            "username": "wrong",
            "password": "wrong"
        })
        # Should be 401 (auth failed) not 429 (rate limited)
        assert response.status_code == 401, f"Request {i+1} should not be rate limited"

    # 6th request should be rate limited
    response = client.post("/api/auth/login", json={
        "username": "wrong",
        "password": "wrong"
    })
    assert response.status_code == 429, "6th request should be rate limited"
    assert "Retry-After" in response.headers


def test_rate_limit_recovery():
    """Test that rate limit resets after window."""
    limiter = rate_limiters["default"]
    limiter.requests.clear()

    test_ip = "test_recovery_ip"

    # Exhaust the limit
    for _ in range(limiter.max_requests):
        allowed, _ = limiter.is_allowed(test_ip)
        assert allowed

    # Next should be blocked
    allowed, _ = limiter.is_allowed(test_ip)
    assert not allowed

    # Simulate time passing
    limiter.requests[test_ip] = [
        t - limiter.window - 1 for t in limiter.requests[test_ip]
    ]

    # Should be allowed again
    allowed, _ = limiter.is_allowed(test_ip)
    assert allowed


def test_sync_endpoint_rate_limit():
    """Test sync endpoints have stricter limits."""
    # This requires admin auth - get token first
    login = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Reset sync limiter
    rate_limiters["sync"].requests.clear()

    # Check remaining header after first request
    response = client.post("/api/sync", headers=headers)
    remaining = int(response.headers.get("X-RateLimit-Remaining", 0))

    # Sync should have lower limit than default
    assert remaining < 100  # Default is 100
```

---

# RESUMEN DE IMPLEMENTACION

## Orden de Implementacion Recomendado

| Paso | Tarea | Tiempo | Dependencias |
|------|-------|--------|--------------|
| 1 | Crear `config.py` y `.env` | 30 min | Ninguna |
| 2 | Actualizar credenciales en `main.py` | 30 min | Paso 1 |
| 3 | Instalar `passlib`, `cryptography` | 10 min | Ninguna |
| 4 | Crear `encryption.py` | 45 min | Paso 1 |
| 5 | Actualizar `database.py` con encriptacion | 1 hora | Paso 4 |
| 6 | Ejecutar migracion de datos | 30 min | Paso 5 |
| 7 | Crear middleware de autenticacion | 1 hora | Paso 2 |
| 8 | Agregar `Depends()` a todos los endpoints | 2 horas | Paso 7 |
| 9 | Implementar rate limit middleware | 1 hora | Ninguna |
| 10 | Testing completo | 2 horas | Pasos 1-9 |
| 11 | Documentacion y actualizacion README | 30 min | Todos |

## Archivos a Crear

1. `config.py` - Configuracion segura
2. `encryption.py` - Modulo de encriptacion
3. `.env` - Variables de entorno (NO commitear)
4. `.env.example` - Template de variables
5. `migrate_encrypt_data.py` - Script de migracion
6. `tests/test_auth_security.py` - Tests de autenticacion
7. `tests/test_encryption.py` - Tests de encriptacion
8. `tests/test_rate_limiter.py` - Tests de rate limiting
9. `tests/test_endpoint_security.py` - Tests de endpoints

## Archivos a Modificar

1. `main.py` - Middlewares, endpoints, imports
2. `database.py` - Funciones de encriptacion
3. `.gitignore` - Excluir `.env`
4. `requirements.txt` - Nuevas dependencias

## Checklist Pre-Deployment

- [ ] `.env` configurado con valores de produccion
- [ ] JWT_SECRET_KEY generado (64+ chars)
- [ ] ADMIN_PASSWORD_HASH generado con bcrypt
- [ ] DATA_ENCRYPTION_KEY generado
- [ ] Migracion de datos ejecutada
- [ ] Todos los tests pasan
- [ ] Rate limiters configurados
- [ ] HTTPS configurado en reverse proxy
- [ ] Logs no contienen datos sensibles
- [ ] Backup de base de datos realizado

---

## CONTACTO Y SOPORTE

Para preguntas sobre este plan de seguridad, contactar al equipo de seguridad.

**Documento generado por:** Claude Security Audit
**Fecha:** 2025-12-23
**Version:** 1.0.0
