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
pytest tests/test_fiscal_year.py -v           # Tests críticos fiscal
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
npm run build                                 # Webpack producción
npm run build:dev                             # Webpack desarrollo
npm run build:watch                           # Webpack modo watch

# Docker
docker-compose -f docker-compose.dev.yml up -d      # Desarrollo
docker-compose -f docker-compose.secure.yml up -d   # Máxima seguridad
docker-compose -f docker-compose.prod.yml up -d     # Producción optimizada

# Database Migrations
alembic revision --autogenerate -m "description"  # Crear nueva migración
alembic upgrade head                              # Aplicar migrations
alembic downgrade -1                              # Rollback último cambio
```

---

## Project Overview

**YuKyuDATA-app** - Sistema de gestión de vacaciones pagadas (有給休暇) con cumplimiento de ley laboral japonesa.

| Stack | Tecnología |
|-------|------------|
| Backend | FastAPI 0.109+ / SQLite / PostgreSQL / PyJWT 2.8+ |
| ORM | SQLAlchemy 2.0+ (migración en progreso) |
| Frontend | Vanilla JS (ES6) + Chart.js + ApexCharts |
| Testing | Pytest (47 test files) + Jest + Playwright |

**Data Sources (deben existir en raíz):**
- `有給休暇管理.xlsm` - Master de vacaciones
- `【新】社員台帳(UNS)T　2022.04.05～.xlsm` - Registro empleados (hojas: DBGenzaiX, DBUkeoiX, DBStaffX)

---

## Architecture

```
Frontend (SPA)                    static/js/app.js + static/src/
       │
       │ REST API (JSON)
       ▼
API Layer (main.py + routes/v1/)  ~50 endpoints, JWT Auth, CSRF, Rate Limiting
       │
       ▼
Service Layer (services/)         14 módulos: fiscal_year, excel, auth, search, reports...
       │
       ▼
Agent System (agents/)            15 agentes especializados + orchestrator
       │
       ▼
ORM Layer (orm/)                  SQLAlchemy 2.0 (Phase 2 migration)
       │
       ▼
Data Layer (database.py)          SQLite/PostgreSQL, backup, audit log
```

### Key Directories

| Directorio | Propósito |
|------------|-----------|
| `routes/v1/` | API endpoints v1 modularizados (19 archivos) |
| `services/` | Lógica de negocio (14 módulos) |
| `agents/` | 15 agentes (compliance, security, testing, memory...) |
| `middleware/` | 9 módulos (CSRF, rate limiting, security headers, auth...) |
| `models/` | 9 modelos Pydantic (employee, vacation, user...) |
| `orm/models/` | 12 modelos SQLAlchemy ORM |
| `repositories/` | 11 repositorios (patrón Repository) |
| `static/src/` | Frontend moderno (41 archivos JS, componentes ES6) |
| `static/js/` | Legacy SPA (app.js - 3,701 líneas) |
| `.claude/skills/` | 15+ skills especializados para Claude |
| `alembic/` | Migraciones de base de datos |

### Estructura de Rutas (Endpoints API)

Los endpoints están organizados en `routes/v1/` por dominio:

```
routes/v1/
├── auth.py                 # Login, logout, refresh tokens
├── employees.py            # CRUD empleados, búsqueda
├── genzai.py              # Empleados de despacho (派遣社員)
├── ukeoi.py               # Empleados contratistas (請負社員)
├── staff.py               # Personal de oficina
├── leave_requests.py      # Solicitudes de vacaciones workflow
├── compliance.py          # Verificación 労働基準法 39条
├── compliance_advanced.py # Reportes avanzados de cumplimiento
├── fiscal.py              # Cálculos fiscal year
├── analytics.py           # Analytics y dashboards
├── reports.py             # Reportes mensuales/anuales
├── export.py              # Exportación Excel/PDF
├── calendar.py            # Calendar events
├── notifications.py       # Sistema de notificaciones
├── health.py              # Health checks
├── system.py              # Estado del sistema
├── yukyu.py               # Sync desde Excel
├── github.py              # Integración GitHub
└── __init__.py            # Inicialización router principal
```

**Cómo agregar un nuevo endpoint:**
1. Crear archivo en `routes/v1/nombre.py`
2. Definir router: `router = APIRouter(prefix="/api/nombre", tags=["nombre"])`
3. Importar en `routes/v1/__init__.py`: `from .nombre import router`
4. El router se registra automáticamente en `main.py`

### Patrón Repository

Cada tabla principal tiene un repositorio en `repositories/`:
- Encapsula acceso a datos (queries SQL)
- Maneja transacciones y context managers
- Interfaz consistente con métodos: `get()`, `list()`, `create()`, `update()`, `delete()`

Ejemplo de uso en services:
```python
from repositories.employee_repository import EmployeeRepository

def get_employee(emp_num: str, year: int):
    repo = EmployeeRepository()
    return repo.get(emp_num, year)  # Usa context manager internamente
```

---

## Business Logic - Fiscal Year (CRÍTICO)

El módulo `services/fiscal_year.py` implementa **労働基準法 第39条** (Ley de Normas Laborales japonesa):

### Configuración
- **Período:** 21日〜20日 (día 21 al 20 del siguiente mes)
- **Carry-over:** Máximo 2 años
- **Acumulación máxima:** 40 días
- **Obligación 5 días:** Empleados con 10+ días deben usar mínimo 5

### Tabla de Otorgamiento
```python
GRANT_TABLE = {
    0.5: 10,  # 6 meses → 10 días
    1.5: 11,  2.5: 12,  3.5: 14,
    4.5: 16,  5.5: 18,  6.5: 20  # máximo
}
```

### Funciones Principales
- `calculate_seniority_years(hire_date)` → años de antigüedad
- `calculate_granted_days(seniority)` → días otorgados
- `apply_lifo_deduction(emp_num, days, year)` → deduce días (más nuevos primero)
- `check_5day_compliance(year)` → verifica cumplimiento de 5 días

---

## Database Design

### Patrón ID Compuesto
Tabla `employees` usa `{employee_num}_{year}` como PK (ej: `001_2025`).

### Tablas Principales
| Tabla | Propósito |
|-------|-----------|
| `employees` | Datos de vacaciones (múltiples registros por empleado/año) |
| `genzai` | Empleados de despacho (派遣社員) |
| `ukeoi` | Empleados contratistas (請負社員) |
| `staff` | Personal de oficina |
| `leave_requests` | Solicitudes (workflow: PENDING → APPROVED/REJECTED) |
| `audit_log` | Trail completo de cambios |
| `notifications` | Sistema de notificaciones |
| `yukyu_usage_detail` | Detalle de uso de vacaciones |

### ORM Migration (Phase 2)
```
database.py           → Legacy SQLite layer (5,732+ líneas)
database_orm.py       → SQLAlchemy ORM wrapper (31 KB)
orm/models/           → 12 modelos ORM
alembic/versions/     → Migraciones versionadas
```

### Patrones de Código
```python
# Conexión segura - SIEMPRE usar context manager
with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE year = ?", (2025,))

# NUNCA concatenar strings en SQL
c.execute(f"SELECT * FROM employees WHERE year = {year}")  # ❌ SQL Injection
c.execute("SELECT * FROM employees WHERE year = ?", (year,))  # ✅ Parameterized

# Para búsquedas - usar ALLOWED_TABLES whitelist
ALLOWED_TABLES = {'employees', 'genzai', 'ukeoi', 'staff'}
if table not in ALLOWED_TABLES:
    raise ValueError(f"Invalid table: {table}")
```

---

## Environment Variables

Copiar `.env.example` a `.env` y configurar:

### Críticas (REQUERIDAS en producción)
```bash
JWT_SECRET_KEY=...              # python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_REFRESH_SECRET_KEY=...      # python -c "import secrets; print(secrets.token_urlsafe(32))"
DATABASE_ENCRYPTION_KEY=...     # python -c "import secrets; print(secrets.token_hex(32))"
```

### Autenticación de Usuarios
```bash
# Opción 1: JSON inline (pequeños equipos)
USERS_JSON='{"admin":{"password":"hash_bcrypt","role":"admin"}}'

# Opción 2: Archivo externo (recomendado)
USERS_FILE=/secure/path/users.json
```

### Principales
```bash
DEBUG=false                 # true para desarrollo (genera credenciales temporales)
DATABASE_TYPE=sqlite        # sqlite o postgresql
DATABASE_URL=sqlite:///./yukyu.db
CORS_ORIGINS=http://localhost:8000
RATE_LIMIT_ENABLED=true
```

### PostgreSQL (Producción)
```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host:5432/yukyu
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

> **IMPORTANTE:** En producción, `DEBUG=false` requiere `JWT_SECRET_KEY` configurado.
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
PATCH /api/leave-requests/{id}/approve   # Deduce días automáticamente
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
| **Ubicación** | `static/js/app.js` | `static/src/` |
| **Líneas de código** | 3,701 líneas | 41 archivos, modular |
| **Patrón** | SPA monolítico | Componentes ES6 |
| **Estado** | Activo en producción | Disponible para nuevas features |
| **Cuándo usar** | Bugs/mantención en features existentes | Nuevas features o refactoring |

**Decisión Rápida:**
- ¿La feature/bug ya existe en app.js? → Edita `static/js/app.js`
- ¿Es una feature completamente nueva? → Usa componentes de `static/src/`
- ¿No estás seguro? → Busca en ambas ubicaciones

### Componentes Modernos (17)

Ubicación: `static/src/components/`

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

**Pages (8):**
- Dashboard, Employees, LeaveRequests, Analytics
- Compliance, Settings, Notifications

**Managers (7):**
- DashboardManager, EmployeesManager, LeaveRequestsManager
- AnalyticsManager, ComplianceManager, PageCoordinator

**Legacy Modules (12):**
| Módulo | Propósito |
|--------|-----------|
| `theme-manager.js` | Gestión de temas (dark/light) |
| `ui-manager.js` | Componentes UI legacy |
| `data-service.js` | Servicios de datos |
| `chart-manager.js` | Gráficos Chart.js/ApexCharts |
| `leave-requests-manager.js` | Gestión de solicitudes |
| `i18n.js` | Internacionalización |
| `sanitizer.js` | Sanitización XSS |
| `auth-manager.js` | Autenticación JWT |

### CSS Design System
| Archivo | Propósito |
|---------|-----------|
| `unified-design-system.css` | Sistema de diseño unificado (Cyan #06b6d4) |
| `yukyu-tokens.css` | Design tokens (colores, espaciado) |
| `login-modal.css` | Estilos del modal de login |

### Temas
- **Dark Mode:** Tema por defecto
- **Light Mode:** Soporte completo (2026-01)
- **Paleta:** Cyan (#06b6d4) como color primario

### PWA Support
- `manifest.json` - PWA manifest
- `sw.js`, `sw-enhanced.js` - Service workers
- `offline.html` - Página offline

### Seguridad Frontend
```javascript
// SIEMPRE usar para contenido dinámico:
escapeHtml(text)        // Escapar HTML
element.textContent     // Texto plano (seguro)

// NUNCA usar:
innerHTML = userInput   // ❌ Vulnerabilidad XSS

// Manejo seguro de localStorage:
try {
    const data = JSON.parse(localStorage.getItem('key'));
} catch (e) {
    localStorage.removeItem('key');  // Limpiar datos corruptos
}
```

---

## Agent System

15 agentes especializados en `agents/`:

| Agente | Propósito | Estado | Endpoints |
|--------|-----------|--------|-----------|
| `orchestrator.py` | Coordinador principal | **ACTIVO** | 3 endpoints |
| `compliance.py` | Verificación 労働基準法 | **ACTIVO** | 6+ endpoints |
| `documentor.py` | Documentación automática | **ACTIVO** | 3 endpoints |
| `memory.py` | Persistencia de contexto | DESARROLLO | Integración parcial |
| `security.py` | Análisis de seguridad | DESARROLLO | Pipeline sin endpoint |
| `nerd.py` | Análisis técnico | DESARROLLO | Pipeline sin endpoint |
| `performance.py` | Optimización | DESARROLLO | Pipeline sin endpoint |
| `testing.py` | Generación de tests | DESARROLLO | Pipeline sin endpoint |
| `ui_designer.py` | Diseño de componentes UI | DESARROLLO | Pipeline sin endpoint |
| `ux_analyst.py` | Análisis UX/accesibilidad | DESARROLLO | Pipeline sin endpoint |
| `data_parser.py` | Parsing Excel/datos | DESARROLLO | Duplica excel_service |
| `figma.py` | Sync sistema de diseño | DESARROLLO | Sin pipeline |
| `canvas.py` | Visualización/dibujo | DESARROLLO | Sin pipeline |

**Estado de Integración:**
- **ACTIVO (3):** Tienen endpoints funcionando en producción
- **DESARROLLO (10):** Código completo pero sin endpoints expuestos
- ~80% del código de agentes no se ejecuta en producción (pendiente exponer pipelines)

Características: Timeout configurado por agente, circuit breaker, auto-cleanup.

---

## Claude Skills

15+ skills en `.claude/skills/`:

**Domain-Specific (YuKyu):**
- `yukyu-compliance` - Verificación de cumplimiento legal
- `yukyu-status` - Monitoreo de estado del proyecto
- `yukyu-start` - Automatización de inicio
- `yukyu-backup` - Gestión de backups

**Parsing & Data:**
- `excel-japanese-parser` - Parser de Excel con caracteres japoneses
- `japanese-labor-compliance` - Guía 労働基準法

**General-Purpose:**
- `app-optimizer` - Optimización de rendimiento
- `code-quality-master` - Refactoring y clean code
- `documentation-generator` - Generación de docs
- `frontend-design` - Diseño UI
- `full-stack-architect` - Decisiones de arquitectura
- `intelligent-testing` - Generación de tests
- `playwright` - Automatización E2E

---

## Security

### Autenticación
- **JWT Auth:** Access 15min + Refresh 30 días
- **Claves:** Desde env vars (NUNCA hardcodeadas)
- **Hashing:** Bcrypt con Passlib

### Protecciones
- **CSRF Protection:** Middleware activo para POST/PUT/DELETE
- **Rate Limiting:** Configurable por endpoint
- **SQL Injection:** Queries parametrizadas + ALLOWED_TABLES whitelist
- **XSS:** Sanitización en frontend con escapeHtml()

### Rate Limits
| Endpoint | Límite |
|----------|--------|
| `/api/auth/login` | 5/min |
| `/api/sync*` | 2/min |
| `/api/reports/*` | 10/min |
| General (auth) | 200/min |

### Configuración Segura
```python
# services/auth_service.py maneja:
# 1. JWT_SECRET_KEY desde env (requerido en producción)
# 2. Usuarios desde USERS_JSON, USERS_FILE, o BD
# 3. En DEBUG=true: genera credenciales temporales seguras

# services/search_service.py:
ALLOWED_TABLES = {'employees', 'genzai', 'ukeoi', 'staff'}  # Whitelist
```

---

## Testing

### Test Structure (47 archivos, 63+ tests)
```
tests/
├── test_api.py                 # 27 API endpoint tests
├── test_audit_fixes.py         # Audit security tests (293 líneas)
├── test_agents_basic.py        # Agent system tests
├── test_fiscal_year.py         # Business logic tests (CRÍTICO)
├── test_api_versioning.py      # API versioning
├── conftest.py                 # Pytest fixtures
├── e2e/                        # Playwright E2E tests
├── integration/                # Integration tests
├── security/                   # Security tests
├── performance/                # Load tests
├── js/                         # Jest frontend tests
└── orm/                        # ORM migration tests
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

# Coverage por módulo
pytest tests/test_api.py --cov=routes --cov-report=term-missing

# Debuggear test que falla
pytest tests/test_api.py::test_sync_employees -v -s  # -s muestra prints
pytest tests/test_fiscal_year.py -v --tb=long         # Stack trace completo
pytest tests/test_api.py -v --pdb                     # Abre debugger en fallo
```

### Coverage Target
- Backend: 80%+ (actual ~98% paths críticos)
- Frontend: Jest coverage configurado

### Debugging Tests
```python
# En un test fallido, usa estas técnicas:

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

Este proyecto tiene pre-commit hooks configurados que se ejecutan **automáticamente** antes de cada commit:

```bash
# Los hooks verifican:
- Trailing whitespace (espacios al final de líneas)
- EOF fixer (archivo termina con newline)
- YAML/JSON syntax validation
- Archivos grandes > 1MB (evitar commits accidentales)
- Secrets detection (API keys, contraseñas)
- No console.log en código producción
```

### Si un Hook Falla

```bash
# 1. El commit se rechaza, ver el error
# 2. Arreglar el problema según el mensaje

# Ejemplos comunes:

# Trailing whitespace
→ Editar archivo y remover espacios al final de líneas

# Archivo JSON/YAML inválido
→ Validar sintaxis: python -m json.tool archivo.json

# Archivo demasiado grande
→ Usar Git LFS: git lfs track "*.xlsm"

# Secrets detectado
→ NO commitar credenciales. Usar variables de entorno o .env.example

# Console.log en producción
→ Remover console.log o usar método diferente de logging

# 3. Stage los cambios y re-intentar commit
git add .
git commit -m "message"
```

### Bypass (Usar con Cuidado)
```bash
# SOLO si estás seguro de qué haces:
git commit --no-verify -m "message"

# No es recomendado - los hooks existen por una razón
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

## ORM Migration Status (Phase 2)

### Estado Actual (Enero 2026)
- **Fase 1 (Completada):** Modelos SQLAlchemy ORM creados en `orm/models/`
- **Fase 2 (En Progreso):** Migración del código legacy a ORM
  - `database.py` (5,732 líneas) sigue siendo la fuente principal
  - `database_orm.py` proporciona wrapper ORM alternativo (31 KB)
  - Alembic migrations configurado pero parcialmente usado

### Cuándo Usar ORM vs Legacy

**Usar ORM (`database_orm.py`):**
```python
# Nuevas features que no existen en database.py
from database_orm import SessionLocal, Employee

def get_new_feature():
    session = SessionLocal()
    employees = session.query(Employee).filter(...).all()
    session.close()
```

**Usar Legacy (`database.py`):**
```python
# Features existentes, bugs, mantención
from database import get_db

def existing_feature():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM employees WHERE ...")
```

### Criterio de Migración
- **Si la función ya existe en database.py:** No migrar ahora, mantener como está
- **Si es feature nueva:** Considera usar ORM
- **Duplicación de código:** El objetivo es consolidar eventualmente a un solo pattern

### Roadmap Futuro
```
2026-Q2: Finalizar Phase 2 (consolidar queries comunes a ORM)
2026-Q3: Deprecate database.py legacy functions
2026-Q4: Full ORM migration
```

---

## CI/CD

### GitHub Workflows (12)
| Workflow | Propósito |
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
| Archivo | Propósito |
|---------|-----------|
| `Dockerfile` | Desarrollo |
| `Dockerfile.prod` | Producción optimizada |
| `Dockerfile.secure` | Máxima seguridad |
| `docker-compose.yml` | Standard (181 líneas) |
| `docker-compose.dev.yml` | Dev con hot-reload (149 líneas) |
| `docker-compose.prod.yml` | Producción (219 líneas) |
| `docker-compose.secure.yml` | Máxima seguridad (569 líneas) |

### Pre-commit Hooks
- Trailing whitespace, EOF fixer
- YAML/JSON validation
- Large file check (1MB max)
- Secrets detection
- No console.log in production

---

## Conventions

### Idiomas
- **Código:** Inglés (variables, funciones, docstrings)
- **UI:** Japonés (labels, mensajes, validaciones)
- **Documentación:** Castellano
- **Commits:** Conventional commits en inglés

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
main  # Producción, PR-merged

# Crear feature branch
git checkout -b feat/feature-name
git checkout -b fix/bug-description
git checkout -b refactor/module-name

# Opcional: agregar session ID si usas Claude Code
git checkout -b claude/feature-name-{sessionId}
```

### Código Python
```python
# Type hints obligatorios para funciones públicas
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
emp = {}  # ❌
fy = 2025  # ❌
```

### Código JavaScript
```javascript
// camelCase para variables y funciones
const employeeData = await fetchEmployeeData(empNum, year);
const calculateVacationBalance = (granted, used) => granted - used;

// CONST por defecto, LET solo cuando necesario cambiar
const maxVacationDays = 40;  // ✅
const userId = user.id;       // ✅

// Módulos ES6
import { Alert, Modal } from '/static/src/components/index.js';
import { fetchAPI } from '/static/src/services/data-service.js';

// NO usar var (legacy)
var data = {};  // ❌
```

### Directorio Naming
- Directorios: `snake_case` (routes, services, models)
- Archivos Python: `snake_case` (employee_repository.py, fiscal_year.py)
- Archivos JS: `kebab-case` (data-service.js, auth-manager.js) o `camelCase` (components)
- Clases: `PascalCase` (EmployeeRepository, AuthService)

### PR/Commits que Fallan
Si los pre-commit hooks rechazan tu commit:

```bash
# Ver qué falló
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

1. **ID Compuesto:** Employees usan `{emp_num}_{year}` como PK, no solo `emp_num`
2. **Período Fiscal:** 21日〜20日, no mes calendario
3. **LIFO Deduction:** Días más nuevos se deducen primero
4. **Excel Headers:** El parser detecta headers dinámicamente, no asumir posición fija
5. **Frontend Dual:** Verificar si el cambio va en `app.js` (legacy) o `static/src/` (moderno)
6. **Theme Support:** Verificar que estilos funcionen en Dark y Light mode
7. **SQL Tables:** Usar ALLOWED_TABLES whitelist para prevenir injection
8. **localStorage:** Envolver JSON.parse en try-catch para manejar corrupción

---

## Recent Changes (2026-01-20)

### Security Audit Fixes (P0-P2) ✅
- **P0 CRITICAL:** SQL Injection prevention con ALLOWED_TABLES whitelist en SearchService
  - Todas las búsquedas verifican tabla contra whitelist
  - Queries parametrizadas obligatorias
- **P1 UI/UX:** Paleta Cyan unificada (#06b6d4), accesibilidad WCAG
  - Sistema de diseño unificado: `unified-design-system.css`
  - Soporte completo Light Mode + Dark Mode
- **P2 Code Quality:** DRY con `_execute_search()` helper, manejo de localStorage corrupto
  - Consolidación de lógica de búsqueda
  - Try-catch wrappers para JSON.parse

### New Features
- **Katakana Display:** Muestra カナ junto a nombres de empleados (hiring name)
- **Dynamic Username:** Username real en audit trail de aprobaciones (no "Unknown User")
- **Fiscal Year Indicator:** Indicador visual en historial de uso (21日〜20日)
- **Full-text Search:** Soporte PostgreSQL en search_service.py (ILIKE queries)
- **Component System:** UIStates (loading/empty/error/skeleton) para estados consistentes
- **PWA Enhancement:** Service Workers mejorados (sw-enhanced.js)

### Code Quality (2026-01)
- Limpieza CSS legacy: -13,884 líneas removidas
- Agent system improvements: timeout per-agent, circuit breaker
- Pre-commit hooks automatizados
- Consolidación de estado frontend (singleton pattern)

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
ls *.xlsm  # Mostrar archivos Excel en directorio raíz

# Verificar codificación (requiere caracteres japoneses)
# Archivos esperados:
# - 有給休暇管理.xlsm
# - 【新】社員台帳(UNS)T　2022.04.05～.xlsm

# Soluciones:
# 1. Cerrar Excel si está abierto (lock de archivo)
# 2. Copiar archivo a raíz exacta: D:\YuKyuDATA-app1.0v\
# 3. Renombrar si tiene caracteres especiales incorrectos
# 4. Verificar en logs del servidor: ERROR reading Excel
```

### CSRF Token Inválido
```
Error: "CSRF token invalid"
Solución:
1. Recargar página (obtiene nuevo token CSRF)
2. Si persiste: Limpiar cookies/localStorage
3. Verificar header X-CSRF-Token en POST requests
4. En frontend, verificar csrf-token.js está cargado
```

### JWT Token Expirado
```
Error: "Token expired" o 401 Unauthorized
Solución:
1. El frontend debe usar refresh token automáticamente
2. Si sigue fallando: Logout + Login nuevamente
3. Verificar en console: auth-manager.js ejecuta refresh
4. Logs: POST /api/auth/refresh debe devolver 200
```

### Tests Fallando
```bash
# Test específico falla localmente
pytest tests/test_fiscal_year.py::test_calculate_granted_days -v -s

# Check si es issue de BD
# Asegurar que database test está limpio
rm yukyu.db  # Recrear BD en memoria para tests

# Fixtures no encontradas
pytest --fixtures  # Listar todas las fixtures

# PostgreSQL requerido pero no disponible
pytest -m "not skip_without_postgres"  # Saltarse tests que requieren PG
```

### Lint Falla en Commit
```bash
# ESLint rechaza código
npm run lint:js  # Auto-fix automático

# Si sigue fallando
npm run lint:js -- --debug  # Ver detalles

# CSS issues
npm run lint:css  # Auto-fix

# YAML/JSON syntax
python -m json.tool archivo.json  # Validar JSON
```

### Problemas de Conexión a BD
```bash
# SQLite (por defecto)
# Verificar archivo existe: yukyu.db
ls -la yukyu.db

# PostgreSQL
# Verificar conexión
psql postgresql://user:pass@localhost:5432/yukyu -c "SELECT 1"

# En logs: "could not connect to server"
# Soluciones:
# 1. Verificar DATABASE_URL correcto en .env
# 2. Iniciar servicio PostgreSQL
# 3. Verificar credenciales usuario/contraseña
```

### Node Modules Corruptos
```bash
# Volver a instalar dependencias
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

# En database.py, verificar:
# CREATE TABLE employees (...) CHARSET=utf8mb4;
```

### Performance Lento
```bash
# Debuggear queries lentas
# 1. Habilitar query logging en database.py
# 2. Ver qué query demora más
# 3. Considerar índices (ALTER TABLE ... ADD INDEX)

# Frontend lento
# 1. Ver bundle size: npm run build:analyze
# 2. Check en DevTools: Performance tab
# 3. Buscar N+1 queries en API responses

# Startup lento
# 1. Migrar a PostgreSQL (SQLite más lento)
# 2. Reducir tamaño de database (backup antiguo)
```

---

## Notes

- Los directorios `basuraa/` y `ThemeTheBestJpkken/` contienen código legacy y están excluidos de CI/CD
- Los modales usan `visibility: hidden` por defecto, clase `.active` para mostrar
- El directorio `.agent/skills/` contiene 184+ ejemplos de skills (no parte del core)
- Storybook disponible para documentación de componentes: `npm run storybook`
- El archivo `.mcp.json` configura context para Claude Code
- Todos los secretos (JWT_SECRET_KEY, DATABASE_ENCRYPTION_KEY) deben estar en .env, NUNCA en código
