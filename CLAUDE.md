# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Hablame en castellano por favor.

> **IMPORTANTE**: Lee también `CLAUDE_MEMORY.md` para contexto de sesiones anteriores, decisiones de arquitectura, errores conocidos y features ya implementadas.

---

## Quick Start

```bash
# Iniciar servidor (opción recomendada en Windows)
script\start_app_dynamic.bat

# O manualmente
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Acceder a la aplicación
http://localhost:8000

# Documentación API
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```

---

## Project Overview

**YuKyuDATA-app** es un sistema de gestión de empleados especializado en cumplimiento de la ley laboral japonesa para vacaciones pagadas (有給休暇).

**Versión actual:** v5.16 (ver `CLAUDE_MEMORY.md` para historial completo)

**Tech Stack:**
- **Backend:** FastAPI + SQLite/PostgreSQL + PyJWT (auth) + Alembic (migrations)
- **Frontend:** Vanilla JavaScript (ES6 modules) + Chart.js + ApexCharts
- **Estilos:** Glassmorphism design system + Design System CSS
- **Testing:** Pytest (backend) + Jest (frontend) + Playwright (E2E)
- **DevOps:** Docker + GitHub Actions CI/CD + Prometheus monitoring

**Data Sources:**
- `有給休暇管理.xlsm` - Master de vacaciones
- `【新】社員台帳(UNS)T　2022.04.05～.xlsm` - Registro de empleados (hojas: DBGenzaiX, DBUkeoiX, DBStaffX)

---

## Development Commands

```bash
# Servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
script\start_app_dynamic.bat  # Recomendado en Windows

# Tests
pytest tests/ -v                                    # Todos los tests (61/62 passing)
pytest tests/test_api.py::test_sync_employees       # Test individual
pytest tests/test_fiscal_year.py -v                 # Tests críticos fiscal
pytest tests/test_lifo_deduction.py -v              # Tests LIFO
pytest tests/test_security.py -v                    # Tests de seguridad
npx jest                                            # Tests frontend (9 suites)
npx playwright test                                 # E2E tests (10 specs)

# Docker
./scripts/docker-dev.sh                             # Iniciar desarrollo
./scripts/docker-dev.sh --stop                      # Detener
docker-compose -f docker-compose.dev.yml up -d      # Alternativa
docker-compose -f docker-compose.secure.yml up -d   # Producción segura

# Verificaciones pre-commit
./scripts/install-hooks.sh                          # Instalar hooks
./scripts/run-checks.sh                             # Verificar manualmente

# Estado del proyecto
python scripts/project-status.py                    # Estado en CLI
# O visitar http://localhost:8000/status            # Dashboard visual

# Dependencias
pip install -r requirements.txt
npm install
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (SPA)                           │
│  static/js/app.js + modules/ (15 ES6 modules)              │
│  Chart.js + ApexCharts | Glassmorphism + Design System     │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────▼───────────────────────────────────────┐
│              API Layer (main.py + routes/)                  │
│  ~50 endpoints | JWT Auth | CSRF Protection | Rate Limiting│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Service Layer                                 │
│  excel_service.py | fiscal_year.py | notifications.py      │
│  reports.py | auth.py | services/*.py                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Agent System (agents/)                         │
│  13 specialized agents | Orchestrator | Memory persistence │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Data Layer (database.py)                     │
│  SQLite/PostgreSQL | Backup system | Audit log | PITR      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Database (yukyu.db)                         │
│  9+ tablas | 15+ índices | FK constraints | Full-text      │
└─────────────────────────────────────────────────────────────┘
```

### Estructura de Directorios

```
YuKyuDATA-app1.0v/
├── main.py                    # FastAPI app principal (6,073 líneas)
├── database.py                # CRUD SQLite/PostgreSQL (2,559 líneas)
├── fiscal_year.py             # Lógica ley laboral japonesa (517 líneas)
├── excel_service.py           # Parser Excel inteligente (921 líneas)
├── auth.py                    # JWT authentication (407 líneas)
├── notifications.py           # Sistema notificaciones (1,200 líneas)
├── reports.py                 # PDF generation (1,104 líneas)
├── excel_export.py            # Excel export (599 líneas)
│
├── routes/                    # API endpoints modularizados (5,932 líneas)
│   ├── employees.py           # CRUD empleados (1,004 líneas)
│   ├── leave_requests.py      # Workflow solicitudes (416 líneas)
│   ├── notifications.py       # Notificaciones API (454 líneas)
│   ├── yukyu.py               # Gestión vacaciones (438 líneas)
│   ├── reports.py             # Generación reportes (403 líneas)
│   ├── system.py              # Estado sistema (404 líneas)
│   ├── analytics.py           # Estadísticas (348 líneas)
│   ├── health.py              # Health checks (399 líneas)
│   ├── compliance.py          # Verificación 5 días (213 líneas)
│   ├── fiscal.py              # Operaciones año fiscal (214 líneas)
│   └── ...                    # 9 archivos más
│
├── agents/                    # Sistema de agentes (11,307 líneas)
│   ├── orchestrator.py        # Coordinación multi-agente (721 líneas)
│   ├── memory.py              # Memoria persistente (1,433 líneas)
│   ├── compliance.py          # Verificación cumplimiento (665 líneas)
│   ├── performance.py         # Análisis rendimiento (789 líneas)
│   ├── security.py            # Auditoría seguridad (885 líneas)
│   ├── testing.py             # Generación tests (970 líneas)
│   ├── ui_designer.py         # Diseño UI (1,023 líneas)
│   ├── ux_analyst.py          # Análisis UX (943 líneas)
│   └── ...                    # 5 agentes más
│
├── static/
│   ├── js/
│   │   ├── app.js             # SPA principal (6,919 líneas)
│   │   ├── app-refactored.js  # Versión refactorizada (16,091 líneas)
│   │   └── modules/           # 15 módulos ES6 (6,689 líneas)
│   ├── css/                   # Estilos (254 KB total)
│   │   ├── main.css           # Principal (78 KB)
│   │   └── design-system/     # Sistema de diseño
│   └── locales/               # i18n (ja/es/en)
│
├── templates/
│   ├── index.html             # SPA entry point (140 KB)
│   ├── status.html            # Dashboard estado (38 KB)
│   └── emails/                # Plantillas email
│
├── tests/                     # 48 archivos de tests
│   ├── test_*.py              # 21 archivos pytest
│   ├── e2e/                   # 10 specs Playwright + POM
│   ├── unit/                  # 9 tests Jest
│   └── conftest.py            # Fixtures pytest
│
├── monitoring/                # Observabilidad (154 KB)
│   ├── health_check.py        # Health checks
│   ├── performance_monitor.py # Métricas rendimiento
│   ├── backup_manager.py      # Gestión backups
│   └── alert_manager.py       # Sistema alertas
│
├── middleware/                # HTTP middleware
│   ├── security.py            # Headers seguridad
│   └── rate_limiter.py        # Rate limiting
│
├── services/                  # Business logic
│   ├── auth_service.py        # Servicio auth
│   └── search_service.py      # Full-text search
│
├── config/                    # Configuración
│   ├── security.py            # Settings seguridad
│   └── secrets_validation.py  # Validación env vars
│
├── .github/workflows/         # CI/CD pipelines
│   ├── ci.yml                 # Integración continua
│   ├── deploy.yml             # Deployment
│   ├── e2e-tests.yml          # Tests E2E
│   └── secure-deployment.yml  # Deploy seguro
│
└── docker/                    # Configuración Docker
    ├── Dockerfile             # Imagen producción
    ├── Dockerfile.secure      # Imagen hardened
    ├── docker-compose.yml     # PostgreSQL cluster
    └── docker-compose.dev.yml # Desarrollo
```

### Archivos Clave

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `main.py` | 6,073 | FastAPI app con ~50 endpoints |
| `database.py` | 2,559 | SQLite/PostgreSQL CRUD, backups, audit log |
| `excel_service.py` | 921 | Parsing inteligente de Excel (medio día, comentarios) |
| `fiscal_year.py` | 517 | **CRÍTICO** - Lógica de ley laboral japonesa |
| `routes/` | 5,932 | 19 módulos de endpoints modularizados |
| `agents/` | 11,307 | 13 agentes especializados |
| `static/js/app.js` | 6,919 | SPA principal con módulos App.* |
| `static/js/modules/` | 6,689 | 15 módulos ES6 |

---

## Business Logic - Fiscal Year (CRÍTICO)

El módulo `fiscal_year.py` implementa **労働基準法 第39条** (Artículo 39 de la Ley de Normas Laborales):

### Configuración

- **Período:** 21日〜20日 (día 21 al 20 del siguiente mes)
- **Carry-over:** Máximo 2 años
- **Acumulación máxima:** 40 días
- **Obligación 5 días:** Empleados con 10+ días deben usar mínimo 5

### Tabla de Otorgamiento (por antigüedad)

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
- `process_year_end_carryover(from_year, to_year)` → traspaso de año

---

## Database Design

### Patrón ID Compuesto

Tabla `employees` usa `{employee_num}_{year}` como PK (ej: `001_2025`).

### Tablas Principales

| Tabla | Propósito |
|-------|-----------|
| `employees` | Datos de vacaciones (múltiples registros por empleado por año) |
| `genzai` | Empleados de despacho (派遣社員) |
| `ukeoi` | Empleados contratistas (請負社員) |
| `staff` | Personal de oficina |
| `leave_requests` | Solicitudes (workflow: PENDING → APPROVED/REJECTED) |
| `yukyu_usage_details` | Fechas individuales de uso |
| `notification_reads` | Estado de lectura por usuario |
| `audit_log` | Trail completo de cambios |
| `users` | Usuarios del sistema |

### Patrones de Código

```python
# Conexión segura
with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE year = ?", (2025,))

# Sincronización idempotente
# Usa INSERT OR REPLACE para evitar duplicados
```

---

## Agent System

El sistema cuenta con 13 agentes especializados en `agents/`:

| Agente | Propósito |
|--------|-----------|
| `OrchestratorAgent` | Coordinación multi-agente, delegación de tareas |
| `MemoryAgent` | Memoria persistente entre sesiones (JSON store) |
| `ComplianceAgent` | Verificación 5 días, alertas expiración |
| `PerformanceAgent` | Optimización queries, detección cuellos de botella |
| `SecurityAgent` | Auditoría vulnerabilidades, análisis auth |
| `TestingAgent` | Generación tests, análisis cobertura |
| `UIDesignAgent` | Análisis componentes, recomendaciones accesibilidad |
| `UXAnalystAgent` | Optimización flujos, análisis conversión |
| `FigmaAgent` | Extracción tokens de diseño, integración Figma |
| `CanvasAgent` | Análisis SVG/Canvas, renderizado charts |
| `DocumentorAgent` | Generación documentación, API docs |
| `DataParserAgent` | Validación datos, análisis calidad |
| `NerdAgent` | Análisis técnico profundo, code quality |

### Uso de Agentes

```python
from agents import get_compliance, get_memory

# Singleton pattern
compliance = get_compliance()
result = compliance.check_5day_compliance(2025)

memory = get_memory()
memory.store_session_context(context)
```

---

## Frontend Architecture

### Patrón Singleton

```javascript
App = {
    state: { data, year, charts, currentView, theme },
    init(), render(), destroy(),
    showDashboard(), showLeaveRequests(), showAnalytics()
}
```

### Módulos ES6 (static/js/modules/)

| Módulo | Líneas | Propósito |
|--------|--------|-----------|
| `ui-manager.js` | 791 | DOM manipulation, event binding |
| `ui-enhancements.js` | 950 | Form validation, tooltips, loading states |
| `data-service.js` | 407 | Cliente API con cache 5 min |
| `chart-manager.js` | 604 | Chart.js + ApexCharts |
| `offline-storage.js` | 792 | IndexedDB para modo offline (PWA) |
| `accessibility.js` | 461 | WCAG 2.1 AA, ARIA labels, keyboard nav |
| `lazy-loader.js` | 466 | Code splitting, intersection observer |
| `virtual-table.js` | 364 | Virtual scrolling para 1000+ filas |
| `i18n.js` | 355 | Internacionalización (ja/es/en) |
| `leave-requests-manager.js` | 425 | Gestión de solicitudes |
| `event-delegation.js` | 246 | Sistema de delegación de eventos |
| `sanitizer.js` | 226 | XSS prevention |
| `export-service.js` | 225 | CSV/Excel export |
| `theme-manager.js` | 122 | Light/dark mode |
| `utils.js` | 255 | Helpers: `escapeHtml()`, `sanitizeInput()` |

### Seguridad Frontend

```javascript
// SIEMPRE usar para contenido dinámico:
escapeHtml(text)        // Escapar HTML
element.textContent     // Texto plano (seguro)

// NUNCA usar:
innerHTML = userInput   // ❌ Vulnerabilidad XSS
```

---

## API Patterns

### Documentación API
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints Principales

```bash
# Sync desde Excel
POST /api/sync                     # Vacaciones
POST /api/sync-genzai              # Empleados despacho
POST /api/sync-ukeoi               # Empleados contratistas
POST /api/sync-staff               # Personal oficina

# Employees CRUD
GET  /api/employees?year=2025      # Listar empleados
GET  /api/employees/{emp}/{year}   # Detalle empleado
PUT  /api/employees/{emp}/{year}   # Actualizar
POST /api/employees/search         # Búsqueda full-text

# Leave requests workflow
POST  /api/leave-requests                    # Crear solicitud
GET   /api/leave-requests?status=PENDING     # Listar
PATCH /api/leave-requests/{id}/approve       # Aprobar (deduce días)
PATCH /api/leave-requests/{id}/reject        # Rechazar
PATCH /api/leave-requests/{id}/revert        # Revertir (restaura días)
# Note: POST también funciona (deprecated, compatibilidad)

# Compliance
GET  /api/compliance/5day?year=2025
GET  /api/expiring-soon?year=2025&threshold_months=3

# Notificaciones
GET   /api/notifications                     # Lista con is_read
PATCH /api/notifications/{id}/read           # Marcar como leída
PATCH /api/notifications/read-all            # Marcar todas
GET   /api/notifications/unread-count        # Conteo no leídas
# Note: POST con rutas antiguas también funciona (deprecated)

# Yukyu Details (edición individual)
GET  /api/yukyu/usage-details/{emp}/{year}  # Obtener detalles
POST /api/yukyu/usage-details               # Crear
PUT  /api/yukyu/usage-details/{id}          # Actualizar
DELETE /api/yukyu/usage-details/{id}        # Eliminar
POST /api/yukyu/recalculate/{emp}/{year}    # Recalcular totales

# Reports
GET  /api/reports/monthly?year=2025&month=1
GET  /api/reports/annual?year=2025
POST /api/reports/pdf                       # Generar PDF

# Analytics
GET  /api/analytics/stats?year=2025
GET  /api/analytics/trends
GET  /api/analytics/department

# Status & Monitoring
GET  /status                                # Dashboard HTML
GET  /api/project-status                    # Estado JSON
GET  /api/health                            # Health check
GET  /api/health/detailed                   # Health detallado
```

---

## Testing

### Estructura de Tests (48 archivos)

```
tests/
├── pytest (21 archivos, 61/62 passing)
│   ├── test_api.py                # Endpoints principales
│   ├── test_fiscal_year.py        # Lógica fiscal (26 KB)
│   ├── test_lifo_deduction.py     # Deducción LIFO (15 KB)
│   ├── test_leave_workflow.py     # Workflow solicitudes (23 KB)
│   ├── test_security.py           # Seguridad (31 KB)
│   ├── test_reports.py            # Reportes PDF/Excel (31 KB)
│   ├── test_database_integrity.py # Integridad DB
│   └── ...
│
├── e2e/ (10 specs Playwright)
│   ├── accessibility.spec.js      # WCAG compliance
│   ├── dashboard.spec.js          # Dashboard flows
│   ├── leave-requests.spec.js     # Workflow solicitudes
│   ├── edit-yukyu.spec.js         # Edición vacaciones
│   ├── bulk-edit.spec.js          # Edición masiva
│   └── pages/                     # Page Object Model
│
└── unit/ (9 tests Jest)
    ├── test-sanitizer.test.js     # XSS prevention
    ├── test-data-service.test.js  # API client
    ├── test-chart-manager.test.js # Charts
    └── ...
```

### Comandos de Tests

```bash
# Backend
pytest tests/ -v                              # Todos
pytest tests/test_fiscal_year.py -v           # Críticos
pytest tests/ --cov=. --cov-report=html       # Coverage

# Frontend
npx jest                                      # Unit tests
npx jest --coverage                           # Con coverage

# E2E
npx playwright test                           # Todos browsers
npx playwright test --headed                  # Con UI
npx playwright test tests/e2e/dashboard.spec.js  # Específico
```

---

## Security Considerations

### Backend
- **CSRF Protection:** Middleware activo para POST/PUT/DELETE
- **JWT Auth:** Tokens con expiración, refresh automático
- **SQL Injection:** Siempre usar parámetros `?` en queries
- **Rate Limiting:** Implementado en endpoints críticos
- **Security Headers:** CSP strict-dynamic, HSTS, X-Frame-Options

### Frontend
- **XSS Prevention:** Usar `escapeHtml()` para todo input de usuario
- **CSP:** Headers configurados (strict-dynamic, no unsafe-inline)
- **Fetch Timeout:** AbortController con 30s timeout
- **Sanitizer:** Módulo dedicado `sanitizer.js`

### Datos Sensibles
- No commitear archivos Excel con datos reales
- `.env` para configuración sensible (no commitear)
- Backups encriptados en producción
- Secrets validation en startup

---

## Docker & Deployment

### Configuraciones Disponibles

| Archivo | Propósito |
|---------|-----------|
| `Dockerfile` | Imagen producción (Python 3.11-slim) |
| `Dockerfile.secure` | Imagen hardened para producción |
| `docker-compose.yml` | PostgreSQL primary + replica |
| `docker-compose.dev.yml` | Desarrollo con SQLite |
| `docker-compose.prod.yml` | Producción con features avanzados |
| `docker-compose.secure.yml` | Producción con seguridad máxima |

### Comandos Docker

```bash
# Desarrollo
./scripts/docker-dev.sh                             # Iniciar
./scripts/docker-dev.sh --stop                      # Detener
docker-compose -f docker-compose.dev.yml up -d      # Alternativa

# Producción
docker-compose -f docker-compose.prod.yml up -d     # Estándar
docker-compose -f docker-compose.secure.yml up -d   # Seguro

# Logs
docker-compose logs -f app
docker-compose logs -f postgres
```

### CI/CD Workflows

| Workflow | Trigger | Propósito |
|----------|---------|-----------|
| `ci.yml` | Push/PR | Lint, tests, security scan |
| `deploy.yml` | Push main | Build, push, deploy |
| `e2e-tests.yml` | PR main | Playwright tests |
| `secure-deployment.yml` | Release | Deploy con verificaciones |
| `memory-sync.yml` | Schedule | Sync CLAUDE_MEMORY.md |

---

## Common Tasks

### Agregar Nueva Columna

1. Actualizar schema en `database.py`
2. Crear migración en `alembic/versions/`
3. Agregar mapping en `excel_service.py`
4. Actualizar respuesta API en `routes/employees.py`
5. Actualizar frontend en `app.js`
6. Agregar tests en `tests/`

### Agregar Nuevo Endpoint

1. Crear archivo en `routes/` o agregar a existente
2. Registrar en `routes/__init__.py`
3. Implementar lógica en service layer si es compleja
4. Agregar validación con Pydantic models
5. Documentar con docstrings (aparece en /docs)
6. Agregar tests

### Agregar Nuevo Agente

1. Crear `agents/nuevo_agente.py`
2. Definir clases y enums necesarios
3. Implementar lógica del agente
4. Agregar factory function `get_nuevo_agente()`
5. Exportar en `agents/__init__.py`
6. Agregar tests

### Debugging

```bash
# Excel parsing
python test_parser.py              # Test parsing
python debug_excel.py              # Inspeccionar datos raw

# Database
sqlite3 yukyu.db ".schema"         # Ver estructura DB
sqlite3 yukyu.db "SELECT * FROM employees LIMIT 5"

# API
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/sync

# Logs
tail -f logs/app.log               # Si existe

# Estado proyecto
python scripts/project-status.py   # CLI dashboard
```

---

## Important Constraints

### Rutas de Excel (deben existir en raíz)

```python
VACATION_EXCEL = Path(__file__).parent / "有給休暇管理.xlsm"
REGISTRY_EXCEL = Path(__file__).parent / "【新】社員台帳(UNS)T　2022.04.05～.xlsm"
```

### Nombres de Hojas (match exacto requerido)

- **DBGenzaiX** - Empleados de despacho
- **DBUkeoiX** - Empleados contratistas
- **DBStaffX** - Personal de oficina

---

## Conventions

### Idiomas
- **Código:** Inglés (variables, funciones, comentarios técnicos)
- **UI:** Japonés (labels, mensajes al usuario)
- **Documentación:** Castellano
- **Commits:** Conventional commits en inglés

### Commits
```bash
feat: Add new feature
fix: Bug fix
docs: Documentation changes
style: Formatting, no code change
refactor: Code restructuring
test: Adding tests
chore: Maintenance tasks
perf: Performance improvements
security: Security fixes
```

### Git Workflow
- Branch principal: `main`
- Features: `claude/feature-name-{sessionId}`
- Fixes: `claude/fix-description-{sessionId}`

### Código Python
```python
# Conexión a DB siempre con context manager
with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE year = ?", (year,))

# Nunca concatenar strings en SQL
c.execute(f"SELECT * FROM employees WHERE year = {year}")  # ❌ MALO
c.execute("SELECT * FROM employees WHERE year = ?", (year,))  # ✅ BIEN

# Agentes con singleton pattern
from agents import get_compliance
compliance = get_compliance()  # ✅ Singleton
```

### Código JavaScript
```javascript
// Usar ES6 modules
import { escapeHtml } from './modules/utils.js';
import { sanitize } from './modules/sanitizer.js';

// Siempre escapar contenido dinámico
element.textContent = data;           // ✅ Seguro
element.innerHTML = escapeHtml(data); // ✅ Si necesitas HTML
element.innerHTML = data;             // ❌ Vulnerabilidad XSS
```

---

## Troubleshooting

### Error: Puerto en uso
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Error: Excel no se puede leer
- Verificar que el archivo existe en la raíz del proyecto
- Verificar nombre exacto (incluyendo caracteres japoneses)
- Cerrar Excel si está abierto

### Error: Import de módulos frontend
- Verificar que el servidor sirve archivos estáticos
- Revisar console del navegador para errores 404
- Verificar paths relativos en imports

### Error: CSRF token inválido
- El token expira después de cierto tiempo
- Recargar la página para obtener nuevo token
- Verificar que el header X-CSRF-Token se envía

### Error: Tests E2E fallan
- Verificar que el servidor está corriendo
- Ejecutar `npx playwright install` para browsers
- Revisar `playwright.config.js` para configuración

### Error: PostgreSQL connection
- Verificar que el contenedor está corriendo
- Revisar variables de entorno en `.env`
- Probar conexión: `docker-compose exec postgres psql -U yukyu`

---

## Claude Session Checklist

### Al iniciar sesión:
1. ✅ Leer `CLAUDE_MEMORY.md` para contexto histórico
2. ✅ Verificar estado git: `git status`, `git log -3`
3. ✅ Revisar TODOs pendientes en `agents/memory_store.json`
4. ✅ Ejecutar `python scripts/project-status.py`

### Antes de implementar:
1. ✅ Verificar si ya existe funcionalidad similar
2. ✅ Revisar patrones establecidos en código existente
3. ✅ Usar `App.editYukyu` como referencia para modales
4. ✅ Revisar tests existentes para el módulo

### Al terminar sesión:
1. ✅ Actualizar `CLAUDE_MEMORY.md` con nuevos aprendizajes
2. ✅ Documentar errores encontrados y soluciones
3. ✅ Agregar features implementadas al historial
4. ✅ Ejecutar tests para verificar nada se rompió

---

## Monitoring & Observability

### Componentes

| Componente | Archivo | Propósito |
|------------|---------|-----------|
| Health Check | `monitoring/health_check.py` | Verificación estado aplicación |
| Performance | `monitoring/performance_monitor.py` | Métricas de rendimiento |
| Backup Manager | `monitoring/backup_manager.py` | Gestión de backups |
| Alert Manager | `monitoring/alert_manager.py` | Sistema de alertas |
| Query Optimizer | `monitoring/query_optimizer.py` | Optimización de queries |

### Endpoints de Monitoreo

```bash
GET /api/health                 # Health check básico
GET /api/health/detailed        # Health con métricas
GET /status                     # Dashboard visual
GET /api/project-status         # Estado JSON completo
```

### Prometheus Metrics

Configuración en `monitoring/prometheus.yml` para:
- Request latency
- Error rates
- Database connection pool
- Cache hit rates

---

## Version History

| Versión | Fecha | Highlights |
|---------|-------|------------|
| v5.16 | 2026-01-16 | Complete test coverage for all routes |
| v5.15 | 2026-01-15 | UI/UX modernization - 100% onclick + inline styles |
| v5.14 | 2026-01-15 | Comprehensive E2E tests for accessibility/compliance |
| v5.13 | 2026-01-14 | Extract inline styles to CSS utilities |
| v5.12 | 2026-01-14 | Event delegation system for modern UI |
| v5.11 | 2026-01-14 | Real deployment, rollback, backup service |
| v5.10 | 2026-01-13 | N+1 query fix and comprehensive tests |
| v5.9 | 2026-01-13 | Phase 1 security, compliance, accessibility |
| v5.8 | 2026-01-12 | Critical audit fixes, E2E tests, healthcheck, CI/CD |
| v5.7 | 2026-01-10 | Route modularization, console.log removal |
| v5.6 | 2026-01-10 | Critical security and accessibility fixes |
| v5.5 | 2026-01-10 | Specialized agents, skills, startup scripts |
| v5.4 | 2026-01-08 | UI/UX Deep Audit & WCAG AA Compliance |

Ver `CLAUDE_MEMORY.md` para historial completo y decisiones de arquitectura.
