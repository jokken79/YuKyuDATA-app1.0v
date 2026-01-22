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
http://localhost:8000/docs   # Swagger UI
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

## Development Commands

```bash
# Tests
pytest tests/ -v                              # Todos
pytest tests/test_fiscal_year.py -v           # Tests críticos fiscal
pytest tests/test_api.py::test_sync_employees # Test individual
npx jest                                      # Frontend unit tests
npx playwright test                           # E2E

# Lint
npm run lint:js                               # ESLint
npm run lint:css                              # Stylelint

# Build
npm run build                                 # Webpack production

# Docker
docker-compose -f docker-compose.dev.yml up -d      # Desarrollo
docker-compose -f docker-compose.secure.yml up -d   # Producción (máxima seguridad)
docker-compose -f docker-compose.prod.yml up -d     # Producción optimizada
```

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

### Arquitectura Dual
| Sistema | Ubicación | Estado |
|---------|-----------|--------|
| **Legacy** | `static/js/app.js` | Activo (producción, 3,701 líneas) |
| **Modern** | `static/src/` | Disponible para nuevas features (41 archivos) |

### Componentes Modernos (17)
```javascript
import { Modal, Alert, Table, Form, Button, Input,
         Select, Card, Badge, Tooltip, Pagination,
         DatePicker, Loader, UIStates } from '/static/src/components/index.js';

Alert.success('保存しました');
Alert.error('エラーが発生しました');
```

### Frontend Pages (8)
- Dashboard, Employees, LeaveRequests, Analytics
- Compliance, Settings, Notifications

### Frontend Managers (7)
- DashboardManager, EmployeesManager, LeaveRequestsManager
- AnalyticsManager, ComplianceManager, PageCoordinator

### Legacy Modules (12)
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

| Agente | Propósito | Tamaño |
|--------|-----------|--------|
| `orchestrator.py` | Coordinador principal | 35.9 KB |
| `compliance.py` | Verificación 労働基準法 | 21.6 KB |
| `security.py` | Análisis de seguridad | 34 KB |
| `memory.py` | Persistencia de contexto | 59.1 KB |
| `testing.py` | Generación de tests | 35.9 KB |
| `performance.py` | Optimización | 30.7 KB |
| `ui_designer.py` | Diseño de componentes UI | 37.2 KB |
| `ux_analyst.py` | Análisis UX/accesibilidad | 38.2 KB |
| `documentor.py` | Documentación automática | 20.6 KB |
| `data_parser.py` | Parsing Excel/datos | 18.1 KB |
| `figma.py` | Sync sistema de diseño | 23.8 KB |
| `canvas.py` | Visualización/dibujo | 26.3 KB |
| `nerd.py` | Análisis técnico | 37.2 KB |

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

### Coverage Target
- Backend: 80%+ (actual ~98% paths críticos)
- Frontend: Jest coverage configurado

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
- **Código:** Inglés (variables, funciones)
- **UI:** Japonés (labels, mensajes)
- **Documentación:** Castellano
- **Commits:** Conventional commits en inglés (`feat:`, `fix:`, `docs:`, `refactor:`)

### Git
- Branch principal: `main`
- Features: `claude/feature-name-{sessionId}`

### Código
```python
# Python - Type hints recomendados
def get_employee(emp_num: str, year: int) -> Optional[Employee]:
    ...

# Docstrings en inglés para funciones públicas
def calculate_granted_days(seniority: float) -> int:
    """Calculate vacation days granted based on seniority years."""
    ...
```

```javascript
// JavaScript - camelCase para variables/funciones
const employeeData = await fetchEmployeeData(empNum, year);

// Uso de módulos ES6
import { Alert } from '/static/src/components/index.js';
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

## Recent Changes (2026-01)

### Security Audit Fixes (P0-P2)
- **P0 CRITICAL:** SQL Injection prevention con ALLOWED_TABLES whitelist en SearchService
- **P1 UI/UX:** Paleta Cyan unificada (#06b6d4), accesibilidad WCAG
- **P2 Code Quality:** DRY con `_execute_search()` helper, manejo de localStorage corrupto

### New Features
- **Katakana Display:** Muestra カナ junto a nombres de empleados
- **Dynamic Username:** Username real en audit trail de aprobaciones
- **Fiscal Year Indicator:** Indicador visual en historial de uso
- **Full-text Search:** Soporte PostgreSQL en search_service.py

---

## Troubleshooting

### Puerto en uso
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

### Excel no se puede leer
- Verificar que el archivo existe en la raíz
- Verificar nombre exacto (caracteres japoneses)
- Cerrar Excel si está abierto

### CSRF token inválido
- Recargar la página para obtener nuevo token
- Verificar header X-CSRF-Token en requests

### JWT Token expirado
- El frontend debe usar refresh token automáticamente
- Verificar auth-manager.js para lógica de refresh

### Database migrations
```bash
# Crear nueva migración
alembic revision --autogenerate -m "description"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Notes

- Los directorios `basuraa/` y `ThemeTheBestJpkken/` contienen código legacy y están excluidos de CI/CD
- Los modales usan `visibility: hidden` por defecto, clase `.active` para mostrar
- El directorio `.agent/skills/` contiene 184+ ejemplos de skills (no parte del core)
- Storybook disponible para documentación de componentes (`npm run storybook`)
