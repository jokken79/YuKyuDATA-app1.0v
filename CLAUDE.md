# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Hablame en castellano por favor.

---

## Quick Start

```bash
# Iniciar servidor (Windows)
script\start_app_dynamic.bat

# O manualmente
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Acceder
http://localhost:8000        # App
http://localhost:8000/docs   # Swagger UI (OpenAPI)
```

---

## Development Commands

```bash
# Tests
pytest tests/ -v                              # Todos los tests
pytest tests/ -v --cov=. --cov-report=html   # Con coverage
pytest tests/test_fiscal_year.py -v           # Tests criticos fiscal
pytest tests/test_api.py::test_sync_employees # Test individual
pytest tests/ -k "test_name" -v               # Filtrar por nombre
npx jest                                      # Frontend unit tests
npx jest --coverage                           # Frontend coverage
npx playwright test                           # E2E tests

# Lint & Format
npm run lint:js                               # ESLint (auto-fix)
npm run lint:css                              # Stylelint (auto-fix)
npm run lint                                  # Ambos

# Build
npm run build                                 # Webpack produccion
npm run build:dev                             # Webpack desarrollo
npm run build:watch                           # Webpack modo watch

# Docker
docker-compose -f docker-compose.dev.yml up -d      # Desarrollo
docker-compose -f docker-compose.secure.yml up -d   # Maxima seguridad
docker-compose -f docker-compose.prod.yml up -d      # Produccion optimizada

# Database Migrations
alembic revision --autogenerate -m "description"  # Crear nueva migracion
alembic upgrade head                              # Aplicar migrations
alembic downgrade -1                              # Rollback ultimo cambio
```

---

## Project Overview

**YuKyuDATA-app** - Sistema de gestion de vacaciones pagadas (有給休暇) con cumplimiento de ley laboral japonesa.

| Stack | Tecnologia |
|-------|------------|
| Backend | FastAPI 0.109+ / SQLite / PostgreSQL / PyJWT 2.8+ |
| ORM | SQLAlchemy 2.0+ (database/ usa ORM internamente) |
| Frontend | Vanilla JS (ES6) + Chart.js + ApexCharts |
| Testing | Pytest (54 test files) + Jest (22 test files) + Playwright |
| Build | Webpack 5.91+ / Babel / PostCSS |
| Node | >= 18.0.0 |

**Data Sources (deben existir en raiz):**
- `有給休暇管理.xlsm` - Master de vacaciones
- `【新】社員台帳(UNS)T　2022.04.05～.xlsm` - Registro empleados (hojas: DBGenzaiX, DBUkeoiX, DBStaffX)

---

## Architecture

```
Frontend (SPA)                    static/js/app.js + static/src/
       |
       | REST API (JSON)
       v
API Layer (main.py + routes/v1/)  ~50 endpoints, JWT Auth, CSRF, Rate Limiting
       |
       v
Service Layer (services/)         14 modulos: fiscal_year, excel, auth, search, reports...
       |
       v
Agent System (agents/)            13 agentes especializados + orchestrator
       |
       v
Database Adapter                  services/database_adapter.py (USE_ORM flag)
       |
       v
Data Layer (database/)            Paquete modular: connection, employees, leave, audit, stats...
       |
       v
ORM Layer (orm/)                  SQLAlchemy 2.0 models (12 modelos)
```

### Key Directories

| Directorio | Proposito |
|------------|-----------|
| `routes/v1/` | API endpoints v1 modularizados (19 archivos) |
| `services/` | Logica de negocio (14 modulos) |
| `agents/` | 13 agentes + orchestrator (compliance, security, testing...) |
| `middleware/` | 10 modulos (CSRF, rate limiting, security headers, auth, error handling...) |
| `models/` | 9 modelos Pydantic (employee, vacation, user...) |
| `orm/models/` | 12 modelos SQLAlchemy ORM |
| `repositories/` | 11 repositorios (patron Repository) |
| `database/` | Paquete modular de acceso a datos (12 modulos, 60+ funciones) |
| `config/` | Configuracion del sistema (secrets_validation, security) |
| `exceptions/` | Excepciones personalizadas |
| `utils/` | 7 utilidades (logger, pagination, file_validator, audit_logger...) |
| `static/src/` | Frontend moderno (46 archivos JS, componentes ES6) |
| `static/js/` | Legacy SPA (app.js - 7,564 lineas) |
| `monitoring/` | Prometheus, Alertmanager, performance monitor |
| `terraform/` | Infraestructura como codigo (IaC) |
| `scripts/` | Scripts de deployment y automatizacion (46 archivos) |
| `.claude/skills/` | 18+ skills especializados para Claude |
| `alembic/` | Migraciones de base de datos (5 versiones) |

### Estructura de Rutas (Endpoints API)

Los endpoints estan organizados en `routes/v1/` por dominio:

```
routes/v1/
+-- auth.py                 # Login, logout, refresh tokens
+-- employees.py            # CRUD empleados, busqueda
+-- genzai.py              # Empleados de despacho (派遣社員)
+-- ukeoi.py               # Empleados contratistas (請負社員)
+-- staff.py               # Personal de oficina
+-- leave_requests.py      # Solicitudes de vacaciones workflow
+-- compliance.py          # Verificacion 労働基準法 39条
+-- compliance_advanced.py # Reportes avanzados de cumplimiento
+-- fiscal.py              # Calculos fiscal year
+-- analytics.py           # Analytics y dashboards
+-- reports.py             # Reportes mensuales/anuales
+-- export.py              # Exportacion Excel/PDF
+-- calendar.py            # Calendar events
+-- notifications.py       # Sistema de notificaciones
+-- health.py              # Health checks
+-- system.py              # Estado del sistema
+-- yukyu.py               # Sync desde Excel
+-- github.py              # Integracion GitHub
+-- __init__.py            # Inicializacion router principal
```

**Como agregar un nuevo endpoint:**
1. Crear archivo en `routes/v1/nombre.py`
2. Definir router: `router = APIRouter(prefix="/api/nombre", tags=["nombre"])`
3. Importar en `routes/v1/__init__.py`: `from .nombre import router`
4. El router se registra automaticamente en `main.py`

### Patron Repository

Cada tabla principal tiene un repositorio en `repositories/`:
- Encapsula acceso a datos (queries SQL)
- Maneja transacciones y context managers
- Interfaz consistente con metodos: `get()`, `list()`, `create()`, `update()`, `delete()`

Ejemplo de uso en services:
```python
from repositories.employee_repository import EmployeeRepository

def get_employee(emp_num: str, year: int):
    repo = EmployeeRepository()
    return repo.get(emp_num, year)  # Usa context manager internamente
```

---

## Business Logic - Fiscal Year (CRITICO)

El modulo `services/fiscal_year.py` implementa **労働基準法 第39条** (Ley de Normas Laborales japonesa):

### Configuracion
- **Periodo:** 21日〜20日 (dia 21 al 20 del siguiente mes)
- **Carry-over:** Maximo 2 anios
- **Acumulacion maxima:** 40 dias
- **Obligacion 5 dias:** Empleados con 10+ dias deben usar minimo 5

### Tabla de Otorgamiento
```python
GRANT_TABLE = {
    0.5: 10,  # 6 meses -> 10 dias
    1.5: 11,  2.5: 12,  3.5: 14,
    4.5: 16,  5.5: 18,  6.5: 20  # maximo
}
```

### Funciones Principales
- `calculate_seniority_years(hire_date)` -> anios de antiguedad
- `calculate_granted_days(seniority)` -> dias otorgados
- `apply_lifo_deduction(emp_num, days, year)` -> deduce dias (mas nuevos primero)
- `check_5day_compliance(year)` -> verifica cumplimiento de 5 dias

---

## Database Design

### Primary Keys
Todas las tablas usan **UUID** como PK (generado por `BaseModel` en `orm/models/base.py`).
Tabla `employees` tiene UniqueConstraint en `(employee_num, year, grant_date)` para preservar todos los periodos de otorgamiento.

### Tablas Principales
| Tabla | Proposito |
|-------|-----------|
| `employees` | Datos de vacaciones (multiples registros por empleado/anio) |
| `genzai` | Empleados de despacho (派遣社員) |
| `ukeoi` | Empleados contratistas (請負社員) |
| `staff` | Personal de oficina |
| `leave_requests` | Solicitudes (workflow: PENDING -> APPROVED/REJECTED) |
| `audit_log` | Trail completo de cambios |
| `notifications` | Sistema de notificaciones |
| `yukyu_usage_details` | Detalle de uso de vacaciones (campo: `use_date`, NO `usage_date`) |

### Database Package (Actual)

El acceso a datos esta modularizado en el paquete `database/` con 12 modulos y 60+ funciones exportadas:

```
database/
+-- __init__.py       # Re-exports publicos (60+ funciones)
+-- connection.py     # get_db(), USE_POSTGRESQL flag, SessionLocal
+-- init_db.py        # Inicializacion de tablas
+-- employees.py      # 16 funciones: save/get/update/reset employees, bulk ops, history
+-- genzai.py         # get_genzai, save_genzai, reset_genzai (派遣社員)
+-- ukeoi.py          # get_ukeoi, save_ukeoi, reset_ukeoi (請負社員)
+-- staff.py          # get_staff, save_staff, reset_staff (事務所)
+-- leave.py          # 9 funciones: CRUD leave requests, approve/reject/cancel/revert
+-- yukyu.py          # 6 funciones: CRUD usage details, monthly summary
+-- audit.py          # log_audit_action, get_audit_logs (filtros avanzados), stats, cleanup
+-- notifications.py  # 7 funciones: CRUD notifications, read tracking
+-- backup.py         # create_backup, list_backups, restore_backup (SQLite)
+-- stats.py          # get_dashboard_stats, get_workplace_distribution
```

**Constraint importante:** Employee unique = `(employee_num, year, grant_date)`, NO solo `(employee_num, year)`.

Uso en el codigo:
```python
# Importar desde el paquete (NO desde archivos individuales)
import database
from database import get_employees, approve_leave_request, get_genzai

# Las funciones usan ORM (SessionLocal) internamente
employees = database.get_employees(year=2025)
database.approve_leave_request(request_id, approved_by="admin")
genzai = database.get_genzai(status="在職中")
```

### Database Adapter

`services/database_adapter.py` proporciona una capa de abstraccion que delega todas las llamadas al paquete `database/`:

```python
from services.database_adapter import get_employees, approve_leave_request

# Todas las llamadas van al paquete database/ (que usa ORM internamente)
employees = get_employees(year=2025)
```

> **Nota:** El flag `USE_ORM` y las rutas a `database_orm.py` ya no aplican.
> El paquete `database/` ya usa SQLAlchemy ORM (SessionLocal) para todas las operaciones.
> El adapter mantiene compatibilidad hacia atras pero internamente todo va a `database/`.

### ORM Models

```
orm/models/
+-- base.py                # Base declarativa SQLAlchemy
+-- employee.py            # Modelo Employee
+-- genzai_employee.py     # Modelo GenzaiEmployee
+-- ukeoi_employee.py      # Modelo UkeoiEmployee
+-- staff_employee.py      # Modelo StaffEmployee
+-- leave_request.py       # Modelo LeaveRequest
+-- audit_log.py           # Modelo AuditLog
+-- notification.py        # Modelo Notification
+-- notification_read.py   # Modelo NotificationRead
+-- user.py                # Modelo User
+-- yukyu_usage_detail.py  # Modelo YukyuUsageDetail
```

### Alembic Migrations

5 migraciones versionadas en `alembic/versions/`:
- `001_initial_schema.py` - Esquema base
- `001_initial_uuid_schema.py` - Esquema con UUIDs
- `002_convert_to_uuid_schema.py` - Conversion a UUIDs
- `003_add_fulltext_search.py` - Full-text search PostgreSQL
- `004_sync_orm_models.py` - Sync con modelos ORM actuales (employees: grant_date/status/kana/hire_date/after_expiry, ukeoi: contract_business, staff: office/visa/address, yukyu: use_date rename + name/month)

### Patrones de Codigo SQL
```python
# NUNCA concatenar strings en SQL
c.execute(f"SELECT * FROM employees WHERE year = {year}")  # PROHIBIDO - SQL Injection
c.execute("SELECT * FROM employees WHERE year = ?", (year,))  # CORRECTO - Parameterized

# Para busquedas - usar ALLOWED_TABLES whitelist
ALLOWED_TABLES = {'employees', 'genzai', 'ukeoi', 'staff'}
if table not in ALLOWED_TABLES:
    raise ValueError(f"Invalid table: {table}")
```

---

## Environment Variables

Copiar `.env.example` a `.env` y configurar:

### Criticas (REQUERIDAS en produccion)
```bash
JWT_SECRET_KEY=...              # python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_REFRESH_SECRET_KEY=...      # python -c "import secrets; print(secrets.token_urlsafe(32))"
DATABASE_ENCRYPTION_KEY=...     # python -c "import secrets; print(secrets.token_hex(32))"
```

### Autenticacion de Usuarios
```bash
# Opcion 1: JSON inline (pequenios equipos)
USERS_JSON='{"admin":{"password":"hash_bcrypt","role":"admin"}}'

# Opcion 2: Archivo externo (recomendado)
USERS_FILE=/secure/path/users.json
```

### Principales
```bash
DEBUG=false                 # true para desarrollo (genera credenciales temporales)
DATABASE_TYPE=sqlite        # sqlite o postgresql
DATABASE_URL=sqlite:///./yukyu.db
CORS_ORIGINS=http://localhost:8000
RATE_LIMIT_ENABLED=true
USE_ORM=false               # true para usar SQLAlchemy ORM (FASE 2)
```

### PostgreSQL (Produccion)
```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host:5432/yukyu
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

> **IMPORTANTE:** En produccion, `DEBUG=false` requiere `JWT_SECRET_KEY` configurado.
> En desarrollo (`DEBUG=true`), se generan claves temporales y usuarios de prueba.

---

## API Patterns

### Endpoints Principales
```bash
# Sync desde Excel
POST /api/sync                     # Vacaciones
POST /api/sync-genzai              # Empleados despacho
POST /api/sync-ukeoi               # Contratistas

# Employees CRUD
GET  /api/employees?year=2025
GET  /api/employees/{emp}/{year}
PUT  /api/employees/{emp}/{year}
GET  /api/employees/search?q=name  # Full-text search (PostgreSQL)

# Leave requests workflow
POST  /api/leave-requests
PATCH /api/leave-requests/{id}/approve   # Deduce dias automaticamente
PATCH /api/leave-requests/{id}/reject

# Compliance
GET  /api/compliance/5day?year=2025
GET  /api/expiring-soon?year=2025&threshold_months=3

# Calendar
GET  /api/calendar/events?year=2025&month=1
POST /api/calendar/events

# Analytics
GET  /api/analytics/dashboard
GET  /api/reports/monthly

# Notifications
GET  /api/notifications
POST /api/notifications/{id}/read

# Health
GET  /api/health
GET  /api/health/detailed
```

---

## Frontend Architecture

### Arquitectura Dual: Legacy vs Modern

| Aspecto | Legacy (app.js) | Modern (static/src/) |
|---------|---|---|
| **Ubicacion** | `static/js/app.js` | `static/src/` |
| **Lineas de codigo** | 7,564 lineas | 46 archivos, modular |
| **Patron** | SPA monolitico | Componentes ES6 |
| **Estado** | Activo en produccion | Disponible para nuevas features |
| **Cuando usar** | Bugs/mantencion en features existentes | Nuevas features o refactoring |

**Decision Rapida:**
- La feature/bug ya existe en app.js? -> Edita `static/js/app.js`
- Es una feature completamente nueva? -> Usa componentes de `static/src/`
- No estas seguro? -> Busca en ambas ubicaciones

### Componentes Modernos (16)

Ubicacion: `static/src/components/`

```javascript
import { Modal, Alert, Table, Form, Button, Input,
         Select, Card, Badge, Tooltip, Pagination,
         DatePicker, Loader, UIStates } from '/static/src/components/index.js';

// Ejemplo de uso
Alert.success('保存しました');
Alert.error('エラーが発生しました');

// Componente Modal
const modal = new Modal({
    title: '確認',
    content: 'よろしいですか？',
    actions: [
        { label: 'キャンセル', action: () => modal.close() },
        { label: '了解', action: () => confirm() }
    ]
});
```

### Estructura Frontend

**Pages (7):**
- Dashboard, Employees, LeaveRequests, Analytics
- Compliance, Settings, Notifications

**Managers (6 + PageCoordinator):**
- DashboardManager, EmployeesManager, LeaveRequestsManager
- AnalyticsManager, ComplianceManager, PageCoordinator

**Legacy Bridge (FASE 3):**

Ubicacion: `static/src/legacy-bridge/`

El bridge permite comunicacion entre el SPA legacy (app.js) y los componentes modernos:
```javascript
// Puente unificado para migrar de legacy a moderno
import { UnifiedBridge } from '/static/src/legacy-bridge/unified-bridge.js';
import { UnifiedStateBridge } from '/static/src/legacy-bridge/unified-state-bridge.js';
```

**Legacy Modules (13):**
| Modulo | Proposito |
|--------|-----------|
| `theme-manager.js` | Gestion de temas (dark/light) |
| `ui-manager.js` | Componentes UI legacy |
| `data-service.js` | Servicios de datos |
| `chart-manager.js` | Graficos Chart.js/ApexCharts |
| `leave-requests-manager.js` | Gestion de solicitudes |
| `i18n.js` | Internacionalizacion (ja/en/es) |
| `sanitizer.js` | Sanitizacion XSS |
| `utils.js` | Utilidades generales |
| `accessibility.js` | Accesibilidad (a11y) |
| `event-delegation.js` | Delegacion de eventos |
| `export-service.js` | Exportacion de datos |
| `offline-storage.js` | Almacenamiento offline |
| `ui-enhancements.js` | Mejoras UI |

### CSS Design System
| Archivo | Proposito |
|---------|-----------|
| `yukyu-design-v4.css` | Design System v4 - Zinc palette, Clean Tech SaaS (ACTUAL) |
| `yukyu-tokens.css` | Design tokens (colores, espaciado, tipografia) |
| `login-modal.css` | Estilos del modal de login (rediseñado v4) |
| `unified-design-system.css` | Sistema de disenio unificado (Cyan #06b6d4) |
| `ui-ux-fixes-2026.css` | Fixes UI/UX 2026 |
| `sidebar-fix.css` | Fix sidebar |
| `contrast-fix.css` | Fix contraste accesibilidad |

### Temas
- **Dark Mode:** Tema por defecto
- **Light Mode:** Soporte completo
- **Paleta:** Cyan (#06b6d4) como color primario

### PWA Support
- `manifest.json` - PWA manifest
- `sw.js`, `sw-enhanced.js` - Service workers
- `offline.html` - Pagina offline

### Internacionalizacion (i18n)
Archivos de locales en `static/locales/`:
- `ja.json` - Japones (principal)
- `en.json` - Ingles
- `es.json` - Espaniol

### Seguridad Frontend
```javascript
// SIEMPRE usar para contenido dinamico:
escapeHtml(text)        // Escapar HTML
element.textContent     // Texto plano (seguro)

// NUNCA usar:
innerHTML = userInput   // PROHIBIDO - Vulnerabilidad XSS

// Manejo seguro de localStorage:
try {
    const data = JSON.parse(localStorage.getItem('key'));
} catch (e) {
    localStorage.removeItem('key');  // Limpiar datos corruptos
}
```

---

## Agent System

13 agentes especializados + orchestrator en `agents/`:

| Agente | Proposito | Estado | Endpoints |
|--------|-----------|--------|-----------|
| `orchestrator.py` | Coordinador principal | **ACTIVO** | 3 endpoints |
| `compliance.py` | Verificacion 労働基準法 | **ACTIVO** | 6+ endpoints |
| `documentor.py` | Documentacion automatica | **ACTIVO** | 3 endpoints |
| `memory.py` | Persistencia de contexto | DESARROLLO | Integracion parcial |
| `security.py` | Analisis de seguridad | DESARROLLO | Pipeline sin endpoint |
| `nerd.py` | Analisis tecnico | DESARROLLO | Pipeline sin endpoint |
| `performance.py` | Optimizacion | DESARROLLO | Pipeline sin endpoint |
| `testing.py` | Generacion de tests | DESARROLLO | Pipeline sin endpoint |
| `ui_designer.py` | Disenio de componentes UI | DESARROLLO | Pipeline sin endpoint |
| `ux_analyst.py` | Analisis UX/accesibilidad | DESARROLLO | Pipeline sin endpoint |
| `data_parser.py` | Parsing Excel/datos | DESARROLLO | Duplica excel_service |
| `figma.py` | Sync sistema de disenio | DESARROLLO | Sin pipeline |
| `canvas.py` | Visualizacion/dibujo | DESARROLLO | Sin pipeline |

**Estado de Integracion:**
- **ACTIVO (3):** Tienen endpoints funcionando en produccion
- **DESARROLLO (10):** Codigo completo pero sin endpoints expuestos
- ~80% del codigo de agentes no se ejecuta en produccion (pendiente exponer pipelines)

Caracteristicas: Timeout configurado por agente, circuit breaker, auto-cleanup.

---

## Claude Skills

18+ skills en `.claude/skills/`:

**Domain-Specific (YuKyu):**
- `yukyu-compliance` - Verificacion de cumplimiento legal
- `yukyu-status` - Monitoreo de estado del proyecto
- `yukyu-start` - Automatizacion de inicio
- `yukyu-backup` - Gestion de backups
- `yukyu-sync` - Sincronizacion de datos
- `yukyu-test` - Testing del proyecto
- `yukyu-vacation-manager` - Gestion de vacaciones
- `yukyu-frontend-dashboard` - Dashboard frontend

**Parsing & Data:**
- `excel-japanese-parser` - Parser de Excel con caracteres japoneses
- `japanese-labor-compliance` - Guia 労働基準法

**General-Purpose:**
- `app-optimizer` - Optimizacion de rendimiento
- `code-quality-master` - Refactoring y clean code
- `documentation-generator` - Generacion de docs
- `frontend-design` - Disenio UI
- `full-stack-architect` - Decisiones de arquitectura
- `intelligent-testing` - Generacion de tests
- `playwright` - Automatizacion E2E

---

## Security

### Autenticacion
- **JWT Auth:** Access 15min + Refresh 30 dias
- **Claves:** Desde env vars (NUNCA hardcodeadas)
- **Hashing:** Bcrypt con Passlib

### Protecciones
- **CSRF Protection:** Middleware activo para POST/PUT/DELETE
- **Rate Limiting:** Configurable por endpoint (rate_limit.py + rate_limiter.py)
- **SQL Injection:** Queries parametrizadas + ALLOWED_TABLES whitelist
- **XSS:** Sanitizacion en frontend con escapeHtml()
- **Security Headers:** Middleware dedicado (security_headers.py)
- **Error Handling:** Exception handler + error handler middleware

### Rate Limits
| Endpoint | Limite |
|----------|--------|
| `/api/auth/login` | 5/min |
| `/api/sync*` | 2/min |
| `/api/reports/*` | 10/min |
| General (auth) | 200/min |

### Configuracion Segura
```python
# services/auth_service.py maneja:
# 1. JWT_SECRET_KEY desde env (requerido en produccion)
# 2. Usuarios desde USERS_JSON, USERS_FILE, o BD
# 3. En DEBUG=true: genera credenciales temporales seguras

# services/search_service.py:
ALLOWED_TABLES = {'employees', 'genzai', 'ukeoi', 'staff'}  # Whitelist
```

---

## Testing

### Test Structure (54 archivos Python + 22 archivos JS)

```
tests/
+-- conftest.py                 # Pytest fixtures compartidas
+-- test_api.py                 # 27 API endpoint tests
+-- test_audit_fixes.py         # Audit security tests
+-- test_agents_basic.py        # Agent system tests
+-- test_fiscal_year.py         # Business logic tests (CRITICO)
+-- test_api_versioning.py      # API versioning
+-- test_auth.py                # Auth tests
+-- test_auth_integration.py    # Auth integration
+-- test_auth_middleware.py      # Auth middleware
+-- test_comprehensive.py       # Comprehensive tests
+-- test_database_adapter.py    # Database adapter (FASE 2)
+-- test_database_compatibility.py
+-- test_database_integrity.py
+-- test_excel_service.py       # Excel service tests
+-- test_exception_handler.py   # Exception handling
+-- test_fiscal_year.py         # Fiscal year (CRITICO)
+-- test_full_text_search.py    # Full-text search
+-- test_leave_workflow.py      # Leave request workflow
+-- test_lifo_deduction.py      # LIFO deduction logic
+-- test_models_*.py            # Pydantic model tests (6 archivos)
+-- test_notifications.py       # Notification tests
+-- test_phase3_compliance.py   # Phase 3 compliance
+-- test_reports.py             # Reports tests
+-- test_routes_*.py            # Route-specific tests (5 archivos)
+-- test_security.py            # Security tests
+-- integration/                # Integration tests (4 archivos)
+--   test_complete_workflows.py
+--   test_data_consistency.py
+--   test_fase4_api.py
+--   test_orm_queries.py
+-- orm/                        # ORM tests
+--   test_phase1_read_operations.py
+-- security/                   # Security tests
+--   test_owasp_validation.py
+-- performance/                # Performance tests
+--   load_test.py
+--   test_performance_benchmark.py
+-- infrastructure/             # Infrastructure tests
+--   test_ci_integration.py
+-- uat/                        # User acceptance tests
+--   test_business_requirements.py
+-- e2e/                        # Playwright E2E tests (12 archivos)
+-- js/                         # Jest frontend tests
+-- unit/                       # Unit tests (JS + HTML)
```

### Pytest Markers
```ini
# pytest.ini
markers =
    unit: Database layer tests
    integration: PostgreSQL integration
    pooling: Connection pool tests
    slow: Long-running tests
    skip_without_postgres: Conditional tests
    flaky: Intermittent failure tests
    e2e: End-to-end tests
```

### Ejecutar Tests con Cobertura

```bash
# Coverage total
pytest tests/ -v --cov=. --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html  # macOS
start htmlcov\index.html # Windows

# Coverage por modulo
pytest tests/test_api.py --cov=routes --cov-report=term-missing

# Debuggear test que falla
pytest tests/test_api.py::test_sync_employees -v -s  # -s muestra prints
pytest tests/test_fiscal_year.py -v --tb=long         # Stack trace completo
pytest tests/test_api.py -v --pdb                     # Abre debugger en fallo
```

### Coverage Target
- Backend: 80%+ (actual ~98% paths criticos)
- Frontend: Jest coverage configurado

### Debugging Tests
```python
# En un test fallido, usa estas tecnicas:

# 1. Print debugging
def test_example():
    result = some_function()
    print(f"Debug: {result}")  # Verlo con pytest -s
    assert result == expected

# 2. Breakpoint (Python 3.7+)
def test_example():
    result = some_function()
    breakpoint()  # Se abre pdb interactivo
    assert result == expected

# 3. pytest fixtures para debugging
def test_example(capfd):
    some_function()
    captured = capfd.readouterr()  # Captura stdout/stderr
    assert "expected" in captured.out
```

---

## Before Committing

### Pre-commit Hooks

Este proyecto tiene pre-commit hooks configurados que se ejecutan **automaticamente** antes de cada commit:

```bash
# Los hooks verifican:
- Trailing whitespace (espacios al final de lineas)
- EOF fixer (archivo termina con newline)
- YAML/JSON syntax validation
- Archivos grandes > 1MB (evitar commits accidentales)
- Secrets detection (API keys, contrasenias)
- No console.log en codigo produccion
```

### Si un Hook Falla

```bash
# 1. El commit se rechaza, ver el error
# 2. Arreglar el problema segun el mensaje

# Ejemplos comunes:

# Trailing whitespace
# -> Editar archivo y remover espacios al final de lineas

# Archivo JSON/YAML invalido
# -> Validar sintaxis: python -m json.tool archivo.json

# Archivo demasiado grande
# -> Usar Git LFS: git lfs track "*.xlsm"

# Secrets detectado
# -> NO commitar credenciales. Usar variables de entorno o .env.example

# Console.log en produccion
# -> Remover console.log o usar metodo diferente de logging

# 3. Stage los cambios y re-intentar commit
git add .
git commit -m "message"
```

### Bypass (Usar con Cuidado)
```bash
# SOLO si estas seguro de que haces:
git commit --no-verify -m "message"

# No es recomendado - los hooks existen por una razon
```

### Antes de Hacer Push
```bash
# 1. Asegurar que tests pasen
pytest tests/ -v

# 2. Lint y format
npm run lint

# 3. Ver commits que se van a pushear
git log origin/main..HEAD

# 4. Finalmente push
git push origin feature-branch
```

---

## ORM Migration Status

### Estado Actual (Febrero 2026)

**FASE 1 (Completada):** Modelos SQLAlchemy ORM creados en `orm/models/` (12 modelos)

**FASE 2 (Completada):** Database Package completo
- `database/` con 12 modulos y 60+ funciones exportadas (todas las rutas cubiertas)
- `services/database_adapter.py` delega al paquete `database/`
- Modulos: connection, init_db, employees, genzai, ukeoi, staff, leave, yukyu, audit, notifications, backup, stats

**FASE 3 (Completada):** Legacy Bridge para frontend
- `static/src/legacy-bridge/` - Puente entre app.js legacy y componentes modernos
- `unified-bridge.js` + `unified-state-bridge.js`
- Permite migrar gradualmente features de app.js a componentes ES6

### Como Usar la Capa de Datos

**Opcion 1 - Importar directamente del paquete (recomendado):**
```python
import database

employees = database.get_employees(year=2025)
database.approve_leave_request(request_id, approved_by="admin")
genzai = database.get_genzai(status="在職中")
years = database.get_available_years()
```

**Opcion 2 - Via Database Adapter (compatibilidad):**
```python
from services.database_adapter import get_employees, approve_leave_request

employees = get_employees(year=2025)
```

> **IMPORTANTE:** Ambas opciones usan ORM (SessionLocal) internamente.
> No existe mas SQL raw. El paquete `database/` ES la implementacion ORM.

---

## CI/CD

### GitHub Workflows (12)
| Workflow | Proposito |
|----------|-----------|
| `ci.yml` | Build, lint, test on PR |
| `deploy.yml` | Production deployment |
| `e2e-tests.yml` | Playwright E2E (non-blocking) |
| `security-scanning.yml` | SAST, dependency checks |
| `performance-test.yml` | Load benchmarks (non-blocking) |
| `advanced-pipeline.yml` | Complex orchestration |
| `blue-green-deploy.yml` | Canary deployments |
| `secure-deployment.yml` | Security-focused deploy |
| `infrastructure-test.yml` | Terraform validation |
| `backup-verify.yml` | Backup integrity |
| `gitops-sync.yml` | GitOps sync |
| `memory-sync.yml` | Agent memory sync |

### Docker (3 Dockerfiles + 4 Compose)
| Archivo | Proposito |
|---------|-----------|
| `Dockerfile` | Desarrollo |
| `Dockerfile.prod` | Produccion optimizada |
| `Dockerfile.secure` | Maxima seguridad |
| `docker-compose.yml` | Standard |
| `docker-compose.dev.yml` | Dev con hot-reload |
| `docker-compose.prod.yml` | Produccion |
| `docker-compose.secure.yml` | Maxima seguridad |

### Monitoring
El directorio `monitoring/` contiene configuracion para:
- Prometheus deployment y alertas
- Alertmanager
- Performance monitor
- Query optimizer
- Backup manager/scheduler

### Infrastructure as Code
`terraform/` contiene configuracion completa (main.tf, modules/, variables.tf, outputs.tf)

### Pre-commit Hooks
- Trailing whitespace, EOF fixer
- YAML/JSON validation
- Large file check (1MB max)
- Secrets detection
- No console.log in production

---

## Conventions

### Idiomas
- **Codigo:** Ingles (variables, funciones, docstrings)
- **UI:** Japones (labels, mensajes, validaciones)
- **Documentacion:** Castellano
- **Commits:** Conventional commits en ingles

### Commit Convention
```bash
# Formato: type(scope): description
# type: feat | fix | docs | refactor | perf | test | chore | style

feat(employees): add katakana display
fix(auth): jwt token refresh logic
docs(claude): improve architecture section
refactor(search): consolidate query builders
perf(dashboard): optimize chart rendering
```

**Scope (opcional pero recomendado):**
- `employees`, `genzai`, `ukeoi`, `staff`
- `auth`, `compliance`, `fiscal`, `reports`
- `database`, `frontend`, `api`, `ui`

### Git Workflow
```bash
# Branch principal
main  # Produccion, PR-merged

# Crear feature branch
git checkout -b feat/feature-name
git checkout -b fix/bug-description
git checkout -b refactor/module-name

# Opcional: agregar session ID si usas Claude Code
git checkout -b claude/feature-name-{sessionId}
```

### Codigo Python
```python
# Type hints obligatorios para funciones publicas
def get_employee(emp_num: str, year: int) -> Optional[Employee]:
    """Calculate vacation days granted based on seniority years.

    Args:
        emp_num: Employee number (e.g., '001')
        year: Fiscal year

    Returns:
        Employee object or None if not found
    """
    ...

# Variables con nombres descriptivos
employee_data = {}
fiscal_year_start = date(2025, 4, 1)

# NO usar nombres cortos ambiguos
emp = {}  # PROHIBIDO
fy = 2025  # PROHIBIDO
```

### Codigo JavaScript
```javascript
// camelCase para variables y funciones
const employeeData = await fetchEmployeeData(empNum, year);
const calculateVacationBalance = (granted, used) => granted - used;

// CONST por defecto, LET solo cuando necesario cambiar
const maxVacationDays = 40;  // CORRECTO
const userId = user.id;       // CORRECTO

// Modulos ES6
import { Alert, Modal } from '/static/src/components/index.js';
import { fetchAPI } from '/static/src/services/data-service.js';

// NO usar var (legacy)
var data = {};  // PROHIBIDO
```

### Directorio Naming
- Directorios: `snake_case` (routes, services, models)
- Archivos Python: `snake_case` (employee_repository.py, fiscal_year.py)
- Archivos JS: `kebab-case` (data-service.js, auth-manager.js) o `camelCase` (components)
- Clases: `PascalCase` (EmployeeRepository, AuthService)

### PR/Commits que Fallan
Si los pre-commit hooks rechazan tu commit:

```bash
# Ver que fallo
git status

# Arreglar problemas
npm run lint  # Auto-fix linting issues
# O editar manualmente los archivos

# Re-commit
git add .
git commit -m "message"  # Los hooks se ejecutan de nuevo
```

---

## Common Pitfalls

1. **Unique Constraint:** Employees usan `(employee_num, year, grant_date)` como UK, no solo `(emp_num, year)`
2. **Periodo Fiscal:** 21日〜20日, no mes calendario
3. **LIFO Deduction:** Dias mas nuevos se deducen primero
4. **Excel Headers:** El parser detecta headers dinamicamente, no asumir posicion fija
5. **Frontend Dual:** Verificar si el cambio va en `app.js` (legacy) o `static/src/` (moderno)
6. **Legacy Bridge:** Usar `static/src/legacy-bridge/` para comunicacion entre sistemas
7. **Theme Support:** Verificar que estilos funcionen en Dark y Light mode
8. **SQL Tables:** Usar ALLOWED_TABLES whitelist para prevenir injection
9. **localStorage:** Envolver JSON.parse en try-catch para manejar corrupcion
10. **Database imports:** Importar desde `database` (paquete), NO buscar `database.py` en raiz
11. **Database adapter:** `database/` y adapter son equivalentes (ambos usan ORM)
12. **YukyuUsageDetail:** Campo es `use_date` (NO `usage_date` - fue renombrado)
13. **Ukeoi ORM:** Usa `contract_business` (NO `dispatch_id` - fue eliminado)
14. **Staff ORM:** Usa `office` (NO `department` - fue eliminado)
15. **AuditLog mapping:** audit.py mapea entity_type->table_name, entity_id->record_id, old_value->old_values, new_value->new_values, additional_info->reason
16. **Excel sheet principal:** `作業者データ　有給` (worksheets[0]), NO Sheet1
17. **Half-day detection:** Usar `detect_leave_type()` + `parse_date_from_cell()` de excel_service.py
18. **grant_date None:** Algunos empleados no tienen grant_date - se usa clave sintetica `row-N`

---

## Recent Changes (2026-02)

### Database Package Completo (60+ funciones)
- 5 modulos nuevos: `genzai.py`, `ukeoi.py`, `staff.py`, `yukyu.py`, `backup.py`
- 4 modulos expandidos: `employees.py` (+15 funciones), `leave.py` (+6), `audit.py` (+3), `notifications.py` (+3)
- 42/42 funciones llamadas por routes ahora implementadas
- Aliases legacy: `log_audit`, `log_action`, `get_audit_log` para compatibilidad
- Alembic migration 004: sync schema con modelos ORM actuales

### Excel Parser Fixes (3 bugs criticos)
- **Data loss fix:** Clave unica cambiada de `(emp_num, year)` a `(emp_num, year, grant_date)` - recuperados 413 registros (14.5%)
- **Half-day fix:** 163 entradas 半休 ahora cuentan 0.5 dias (no 1.0) - 81.5 dias ya no se sobrecontaban
- **ORM model sync:** Ukeoi=contract_business, Staff=office/visa/etc, YukyuUsageDetail=use_date
- 6 columnas nuevas parseadas: status, kana, hire_date, after_expiry, grant_date, leave_type

### Design System v4 - Zinc + Cyan
- `yukyu-design-v4.css` reemplaza v3
- Paleta Zinc (fondos), Cyan (#06b6d4) primario, Inter font
- Login modal rediseñado
- Archivos legacy movidos a `LIXO/`

### Project Structure Reorganization
- 42 archivos reorganizados segun mejores practicas
- Scripts movidos a `scripts/{analysis,debug,fixes,data,utils,windows}/`
- Docs movidos a `docs/`
- Debug output y backups a `LIXO/`

### Repository Fixes
- `ukeoi_repository.py`: `get_by_dispatch()` -> `get_by_contract_business()`
- `staff_repository.py`: `get_by_department()` -> `get_by_office()`
- `database_adapter.py`: eliminada referencia muerta a `database_orm`

### Previous Changes
- FASE 3 Legacy Bridge completada (`static/src/legacy-bridge/`)
- API v0 -> v1 migracion completada
- Security Audit P0-P2 fixes (SQL Injection, Cyan palette, DRY)
- Features: Katakana, Dynamic Username, Fiscal Year Indicator, Full-text Search, UIStates, PWA
- CSS legacy cleanup: -13,884 lineas
- Agent system: timeout per-agent, circuit breaker
- Pre-commit hooks automatizados

---

## Troubleshooting

### Puerto en Uso
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>

# O simplemente cambiar puerto en uvicorn
python -m uvicorn main:app --port 8001
```

### Excel no se puede Leer
```bash
# Verificar archivo existe con nombre exacto
ls *.xlsm  # Mostrar archivos Excel en directorio raiz

# Archivos esperados:
# - 有給休暇管理.xlsm
# - 【新】社員台帳(UNS)T　2022.04.05～.xlsm

# Soluciones:
# 1. Cerrar Excel si esta abierto (lock de archivo)
# 2. Copiar archivo a raiz del proyecto
# 3. Renombrar si tiene caracteres especiales incorrectos
# 4. Verificar en logs del servidor: ERROR reading Excel
```

### CSRF Token Invalido
```
Error: "CSRF token invalid"
Solucion:
1. Recargar pagina (obtiene nuevo token CSRF)
2. Si persiste: Limpiar cookies/localStorage
3. Verificar header X-CSRF-Token en POST requests
4. En frontend, verificar csrf-token.js esta cargado
```

### JWT Token Expirado
```
Error: "Token expired" o 401 Unauthorized
Solucion:
1. El frontend debe usar refresh token automaticamente
2. Si sigue fallando: Logout + Login nuevamente
3. Verificar en console: auth-manager.js ejecuta refresh
4. Logs: POST /api/auth/refresh debe devolver 200
```

### Tests Fallando
```bash
# Test especifico falla localmente
pytest tests/test_fiscal_year.py::test_calculate_granted_days -v -s

# Check si es issue de BD
rm yukyu.db  # Recrear BD en memoria para tests

# Fixtures no encontradas
pytest --fixtures  # Listar todas las fixtures

# PostgreSQL requerido pero no disponible
pytest -m "not skip_without_postgres"  # Saltarse tests que requieren PG
```

### Lint Falla en Commit
```bash
# ESLint rechaza codigo
npm run lint:js  # Auto-fix automatico

# Si sigue fallando
npm run lint:js -- --debug  # Ver detalles

# CSS issues
npm run lint:css  # Auto-fix

# YAML/JSON syntax
python -m json.tool archivo.json  # Validar JSON
```

### Problemas de Conexion a BD
```bash
# SQLite (por defecto)
ls -la yukyu.db

# PostgreSQL
psql postgresql://user:pass@localhost:5432/yukyu -c "SELECT 1"

# Soluciones:
# 1. Verificar DATABASE_URL correcto en .env
# 2. Iniciar servicio PostgreSQL
# 3. Verificar credenciales usuario/contrasenia
```

### Node Modules Corruptos
```bash
rm -rf node_modules package-lock.json
npm install

# Limpiar cache npm
npm cache clean --force
npm install
```

### Charset Issues (Caracteres Japoneses)
```python
# En Python, asegurar UTF-8
import sys
print(sys.getdefaultencoding())  # Debe ser 'utf-8'

# En Excel parser
from openpyxl import load_workbook
wb = load_workbook('有給休暇管理.xlsm')
```

### Performance Lento
```bash
# Debuggear queries lentas
# 1. Habilitar query logging en database/connection.py
# 2. Ver que query demora mas
# 3. Considerar indices (ALTER TABLE ... ADD INDEX)

# Frontend lento
# 1. Ver bundle size: npm run build:analyze
# 2. Check en DevTools: Performance tab
# 3. Buscar N+1 queries en API responses
```

---

## Notes

- Los directorios `basuraa/`, `ThemeTheBestJpkken/` y `LIXO/` contienen codigo legacy y estan excluidos de CI/CD
- Los modales usan `visibility: hidden` por defecto, clase `.active` para mostrar
- El directorio `.agent/skills/` contiene 187 ejemplos de skills (no parte del core)
- Storybook disponible para documentacion de componentes: `npm run storybook`
- El archivo `.mcp.json` configura context para Claude Code
- Todos los secretos (JWT_SECRET_KEY, DATABASE_ENCRYPTION_KEY) deben estar en .env, NUNCA en codigo
- `main.py` (369 lineas) es el punto de entrada FastAPI - importa desde `database` (paquete)
- El directorio `api/` contiene endpoints legacy (pre-v1), usar `routes/v1/` para nuevo desarrollo
