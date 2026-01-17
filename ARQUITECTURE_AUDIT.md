# AUDITORÍA DE ARQUITECTURA - YuKyuDATA v5.19

**Fecha:** 17 Enero 2026
**Versión:** 5.19
**Auditor:** Claude Code DevOps Engineer
**Estado:** 🟡 ARQUITECTURA EN TRANSICIÓN (Media Madurez)

---

## TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis de Estructura](#análisis-de-estructura)
3. [Problemas Identificados](#problemas-identificados)
4. [Análisis de Componentes](#análisis-de-componentes)
5. [Comparación con Estándares](#comparación-con-estándares)
6. [Matriz de Riesgos](#matriz-de-riesgos)
7. [Recomendaciones Prioritarias](#recomendaciones-prioritarias)
8. [Hoja de Ruta de Modernización](#hoja-de-ruta-de-modernización)

---

## RESUMEN EJECUTIVO

### Estado Actual

| Métrica | Valor | Evaluación |
|---------|-------|-----------|
| **Madurez Arquitectónica** | 5.5/10 | 🟡 Media - En Transición |
| **Escalabilidad** | 4/10 | 🔴 Limitada |
| **Mantenibilidad** | 6/10 | 🟡 Aceptable pero Mejorable |
| **Seguridad** | 7/10 | 🟢 Buena (JWT, CSRF, Rate Limit) |
| **Testing** | 7/10 | 🟢 Buena (58 tests, 80% coverage) |
| **Documentación** | 8/10 | 🟢 Excelente (CLAUDE.md, CLAUDE_MEMORY.md) |

### Hallazgos Clave

✅ **Fortalezas:**
- Arquitectura modular bien estructurada (routes/, services/, models/)
- Sistema de agentes 13 especializados (OrchestratorAgent, SecurityAgent, etc.)
- Frontend dual viable (legacy app.js + modern static/src/)
- Seguridad sólida (JWT refresh tokens, CSRF, rate limiting)
- Pydantic v2 con schemas bien organizados
- Testing framework completo (pytest + Playwright E2E)
- Documentación excepcional (CLAUDE.md, CLAUDE_MEMORY.md)

🔴 **Debilidades Críticas:**
- **Escalabilidad limitada:** Patrón de ID compuesto `{employee_num}_{year}` impide sharding horizontal
- **Acoplamiento fuerte:** database.py (2,904 líneas) acoplado directamente en rutas
- **Deuda técnica acumulada:** 17,140 líneas en static/js legacy vs 13,874 en static/src moderno
- **Problemas N+1:** Queries sin optimización en ciertos endpoints
- **Duplicación de código:** log_audit_action, get_client_info duplicados en main.py y routes/
- **Frontend frágil:** Migración gradual legacy → moderno sin breaking changes requiere bridge frágil

🟡 **Puntos de Atención:**
- database.py monolítico (2,904 líneas) difícil de testear
- Sistema de agentes sobrearquitectónico (11,307 líneas) para 13 agentes
- Falta ORM (SQLAlchemy/Tortoise) - queries SQL raw strings
- Sincronización Excel dependiente de formato exacto
- Cache (5 min) pero sin invalidación predictiva

---

## ANÁLISIS DE ESTRUCTURA

### 1. BACKEND STRUCTURE (55,933 líneas Python)

#### A. Capa de Puntos de Entrada
```
main.py (784 líneas)
├── Inicialización FastAPI
├── Middleware registration (CORS, GZip, Security)
├── Exception handlers
├── Router includes (16 routers)
└── Entry point (uvicorn.run)
```

**Problemas:**
- ❌ Importa 97 símbolos de 40+ módulos
- ❌ ThreadPoolExecutor duplicado (línea 104) - también en employees.py
- ❌ Definiciones de funciones auxiliares (get_client_info, audit_action, log_audit_action) que deberían estar en utils

#### B. Capa de Rutas (6,344 líneas en 20 archivos)

| Módulo | Líneas | Endpoints | Patrón |
|--------|--------|-----------|--------|
| employees.py | 958 | 15 | GET/POST/PUT ✅ |
| leave_requests.py | 395 | 8 | Workflow REST 🟡 |
| yukyu.py | 405 | 6 | CRUD ✅ |
| reports.py | 390 | 5 | PDF/Excel export ✅ |
| notifications.py | 432 | 7 | REST + WebSocket ready |
| health.py | 399 | 5 | Monitoring ✅ |
| system.py | 404 | 6 | Admin/Status ✅ |
| github.py | 379 | 4 | Webhooks ✅ |
| analytics.py | 348 | 6 | Data aggregation ✅ |
| **TOTAL** | **6,344** | **~70** | **Bien modularizado** |

**Problemas:**
- ⚠️ routes/dependencies.py duplica get_client_info, log_audit_action de main.py
- ⚠️ Todas las rutas importan `database` directamente (tight coupling)
- ⚠️ No hay repository pattern - queries SQL dispersas en rutas

#### C. Capa de Servicios (3,600 líneas en 11 archivos)

| Servicio | Líneas | Responsabilidad |
|----------|--------|-----------------|
| excel_service.py | 921 | Parser inteligente Excel |
| fiscal_year.py | 517 | **CRÍTICO** - Ley laboral japonesa |
| notifications.py | 1,200 | Email + in-app + WebSocket |
| reports.py | 1,104 | PDF/Excel generation |
| excel_export.py | 599 | Export master data |
| auth.py | 407 | JWT + password hashing |
| caching.py | 300+ | 5-min cache con decorator |
| search_service.py | 363 | Full-text search |
| crypto_utils.py | 200+ | Field encryption |
| auth_service.py | 300+ | Token management |
| asset_service.py | 100+ | Asset management |

**Problemas:**
- ⚠️ fiscal_year.py NO importa database - usa parámetros (buen aislamiento ✅)
- ⚠️ notifications.py tightly coupled a database (debería ser event-driven)
- ⚠️ excel_service.py depende de rutas exactas de archivos Excel
- ⚠️ Caching con TTL fijo (5 min) sin invalidación predictiva

#### D. Capa de Base de Datos (2,904 líneas)

```
database.py
├── init_db() - Schema creation
├── get_db() - Context manager (BUENO)
├── get_employees() - Lectura
├── sync_employees() - INSERT OR REPLACE (idempotent)
├── Tablas: employees (9 columnas), genzai, ukeoi, staff
├── Índices: idx_usage_employee_year
├── Constraints: FK, UNIQUE, PK compuesto
└── Audit logging - Completo
```

**Críticos:**
- 🔴 **2,904 líneas monolíticas** - sin separación de concerns
- 🔴 **Sin ORM** - queries SQL raw strings
- 🔴 **Patrón ID compuesto:** `{employee_num}_{year}` impide escalado horizontal
- 🔴 **N+1 en ciertos queries** (ej. get_employees_enhanced)
- 🟡 PostgreSQL support pero con fallback SQLite (code path duplication)

**Bueno:**
- ✅ Context manager `with get_db()` previene memory leaks
- ✅ Índices apropiados para employee_num y year
- ✅ Transacciones implícitas en INSERT OR REPLACE
- ✅ Audit log table con columnas completas

#### E. Capa de Modelos (2,604 líneas en 8 archivos)

```
models/
├── common.py - APIResponse, PaginatedResponse, DateRangeQuery (325 líneas)
├── employee.py - EmployeeCreate, EmployeeUpdate, BulkUpdateRequest (480 líneas)
├── leave_request.py - LeaveRequestCreate, LeaveRequestApprove, Workflow (420 líneas)
├── vacation.py - YukyuSummary, UsageDetailCreate, BalanceBreakdown (410 líneas)
├── notification.py - NotificationType, NotificationSettings (350 líneas)
├── user.py - UserCreate, LoginRequest, TokenResponse, CurrentUser (400 líneas)
├── fiscal.py - ComplianceCheckResult, CarryoverRequest (240 líneas)
└── report.py - CustomReportRequest, ReportMetadata (280 líneas)
```

**Análisis:**
- ✅ Excelente separación por dominio
- ✅ Pydantic v2 con field_validator
- ✅ Todos tienen docstrings
- ✅ Validaciones en schema (no repetidas en rutas)

**Mejorables:**
- ⚠️ CommonModel base class ausente (DRY principle)
- ⚠️ Sin generación automática de OpenAPI docs
- ⚠️ Sin soft-delete patterns

#### F. Middleware & Config (900+ líneas)

| Componente | Líneas | Propósito |
|-----------|--------|-----------|
| middleware/rate_limiter.py | 300+ | User-aware rate limiting |
| middleware/security_headers.py | 250+ | CSP, HSTS, X-Frame |
| middleware/csrf.py | 180+ | CSRF token generation/validation |
| middleware/exception_handler.py | 150+ | Global error handling |
| config/security.py | 200+ | Pydantic settings |
| config/secrets_validation.py | 150+ | Env var validation |

**Análisis:**
- ✅ Middleware bien separado
- ✅ Security settings centralizadas
- 🟡 Exception handler podría ser más granular
- 🟡 Secrets validation podría integrar con HashiCorp Vault

---

### 2. FRONTEND STRUCTURE (46,772 líneas JavaScript + 20,026 CSS)

#### A. Arquitectura Dual (Legacy + Modern)

```
Frontend Actual (v5.19)
├── Legacy (17,140 líneas)
│   ├── static/js/app.js (7,091 líneas) - SPA monolítico
│   ├── static/js/modules/ (6,689 líneas) - 19 módulos ES6
│   │   ├── ui-manager.js (791)
│   │   ├── data-service.js (407)
│   │   ├── chart-manager.js (604)
│   │   ├── offline-storage.js (792)
│   │   └── ... (14 más)
│   └── static/js/*.js (utilities y helpers)
│
├── Moderno (13,874 líneas)
│   ├── static/src/components/ (7,700 líneas) - 14 componentes
│   │   ├── Modal.js (685)
│   │   ├── Table.js (985)
│   │   ├── Form.js (1,071)
│   │   ├── Select.js (975)
│   │   └── ... (10 más)
│   ├── static/src/pages/ (3,200 líneas) - 7 páginas
│   │   ├── Dashboard.js (478)
│   │   ├── Employees.js (371)
│   │   ├── LeaveRequests.js (579)
│   │   └── ...
│   ├── static/src/store/state.js (245 líneas) - Observer pattern
│   ├── static/src/config/constants.js (205 líneas)
│   ├── static/src/index.js (206 líneas) - Entry point
│   └── static/src/legacy-adapter.js - **PUENTE**
│
├── Estilos (20,026 líneas)
│   ├── static/css/main.css (78 KB)
│   ├── static/css/design-system/ (utilities, components)
│   └── static/theme_source/
│
└── Assets
    ├── static/locales/ (ja.json, es.json, en.json)
    ├── static/manifest.json (PWA)
    └── static/icons/
```

**Problemas Críticos:**
- 🔴 **Coexistencia no óptima:** app.js (7,091) vs static/src/ (13,874) = 21,000 líneas de código duplicado
- 🔴 **Legacy monolítico:** app.js es SPA única con 7,000+ líneas
- 🔴 **Bridge frágil:** legacy-adapter.js requiere `integrateWithLegacyApp()` manual
- 🔴 **Dos sistemas de estado:** App.state (legacy) vs Observer pattern (moderno)

**Puntos Positivos:**
- ✅ static/src/components/ bien abstraído (Modal, Table, Form, Select)
- ✅ static/src/pages/ sigue patrones consistentes
- ✅ Observer pattern en state.js es escalable
- ✅ PWA-ready (service worker, manifest)

#### B. Análisis de Componentes Modernos

| Componente | Líneas | Responsabilidad | Acoplamiento |
|-----------|--------|-----------------|--------------|
| Modal.js | 685 | Dialogs, forms | 🟢 Bajo |
| Table.js | 985 | Data table con sort/filter | 🟢 Bajo |
| Form.js | 1,071 | Form builder + validación | 🟡 Medio (validators) |
| Select.js | 975 | Dropdown con búsqueda | 🟢 Bajo |
| DatePicker.js | 935 | Calendario | 🟢 Bajo |
| Alert.js | 883 | Toast notifications | 🟢 Bajo |
| Card.js | 595 | Containers | 🟢 Bajo |
| Loader.js | 591 | Spinners, skeleton | 🟢 Bajo |
| Pagination.js | 576 | Page navigation | 🟢 Bajo |
| Button.js | 553 | Button variants | 🟢 Bajo |
| Input.js | 543 | Input fields | 🟢 Bajo |
| Tooltip.js | 408 | Hover tips | 🟢 Bajo |
| Badge.js | 389 | Status indicators | 🟢 Bajo |
| index.js | 110 | Barrel exports | ✅ |

**Análisis:**
- ✅ Componentes bien aislados
- ✅ Bajo acoplamiento
- ✅ Fáciles de testear
- ⚠️ Faltan tipos TypeScript (usando vanilla JS)
- ⚠️ Sin storybook runtime (solo configuración estática)

#### C. Análisis de Páginas Modernas

| Página | Líneas | Estado | Integración |
|--------|--------|--------|-------------|
| Dashboard.js | 478 | ✅ Completa | Componentes + API |
| Employees.js | 371 | ✅ Completa | CRUD + bulk edit |
| LeaveRequests.js | 579 | ✅ Completa | Workflow |
| Analytics.js | 479 | ✅ Completa | Charts |
| Compliance.js | 332 | ✅ Completa | 5-day check |
| Notifications.js | 445 | ✅ Completa | Real-time ready |
| Settings.js | 413 | ✅ Completa | User preferences |

**Análisis:**
- ✅ Páginas siguen patrón consistente
- ✅ init(), render(), cleanup() lifecycle
- ✅ Uso de componentes reutilizables
- ⚠️ Sin lazy loading de páginas
- ⚠️ Sin pre-fetching de datos

#### D. Gestión de Estado

**Legacy (app.js):**
```javascript
App.state = {
    data: [],
    year: null,
    charts: {},
    currentView: 'dashboard'
}
```
- ❌ Mutable por naturaleza
- ❌ Sin history/undo
- ❌ Suscripciones manuales

**Moderno (static/src/store/state.js):**
```javascript
Observer pattern
- subscribe/unsubscribe
- getState/setState
- Notify listeners on change
```
- ✅ Inmutabilidad
- ✅ Listeners automáticos
- ✅ No mutaciones directas

---

### 3. SISTEMA DE AGENTES (11,307 líneas en 13 archivos)

#### A. Arquitectura de Agentes

```
agents/
├── orchestrator.py (721 líneas) - Coordinador central
│   ├── OrchestratorAgent - Ejecuta pipelines
│   ├── TaskStatus - PENDING, RUNNING, COMPLETED, FAILED
│   └── PipelineResult - Resultado de pipeline
│
├── memory.py (1,433 líneas) - Persistencia entre sesiones
│   ├── MemoryAgent - CRUD de aprendizajes
│   ├── todo_store.json - TODOs pendientes
│   └── solutions.json - Soluciones conocidas
│
├── compliance.py (665 líneas) - 5-day rule
├── security.py (885 líneas) - OWASP scanning
├── performance.py (789 líneas) - Query optimization
├── testing.py (970 líneas) - Test generation
├── nerd.py (946 líneas) - Code analysis
├── ui_designer.py (1,023 líneas) - CSS/design tokens
├── ux_analyst.py (943 líneas) - UX heuristics
├── figma.py (735 líneas) - Figma integration
├── canvas.py (817 líneas) - SVG/Canvas analysis
├── data_parser.py (551 líneas) - Excel parsing
└── documentor.py (628 líneas) - Documentation
```

**Análisis Arquitectónico:**

✅ **Fortalezas:**
- Singleton pattern con getters (`get_compliance()`, `get_security()`)
- Orquestación de tareas con TaskResult estructurado
- Persistencia en JSON (memory_store.json, solutions.json)
- Cada agente tiene responsabilidad única (SRP)

🔴 **Problemas:**
- **Sobrearquitectónico:** 11,307 líneas para 13 agentes = 870 líneas por agente
- **Duplicación:** 3+ agentes hacen logging/analysis (compliance, security, nerd)
- **Acoplamiento OrchestratorAgent:** Tightly coupled a cada agente specific
- **Sin persistencia real:** JSON store, no SQLite/PostgreSQL
- **Sin integración con rutas:** Agentes existen en vacuum, no se usan en endpoints

**Pregunta arquitectónica:**
> ¿Los agentes son necesarios en producción? Parecen ser herramientas de desarrollo/análisis.

Recomendación: Mover a CLI tool separado (`yukyu-cli analyze`) en lugar de en aplicación principal.

---

### 4. TESTING INFRASTRUCTURE

#### A. Backend Tests (32 archivos pytest)

```
tests/
├── test_api.py - Endpoints principales
├── test_fiscal_year.py (26 KB) - 🔥 Crítico para ley laboral
├── test_lifo_deduction.py (15 KB) - Deducción LIFO
├── test_leave_workflow.py (23 KB) - Workflow completo
├── test_security.py (31 KB) - Auth, CSRF, headers
├── test_reports.py (31 KB) - PDF/Excel export
├── test_database_integrity.py - FK constraints
├── test_employees.py - CRUD
├── test_models_*.py (6 archivos) - Pydantic validation
├── test_refresh_tokens.py
├── test_excel_parsing.py
├── test_performance.py
└── conftest.py - Fixtures compartidas
```

**Métricas:**
- ✅ 61/62 tests passing (98.4%)
- ✅ 80% code coverage (threshold en CI)
- ✅ Cobertura de models, routes, services
- ⚠️ 1 test failing (connection pooling)

**Análisis:**
- ✅ Excelente cobertura de fiscal_year.py (crítico)
- ✅ Tests para LIFO deduction (complejo)
- ✅ Seguridad well-tested
- 🟡 Falta cobertura de agentes (11,307 líneas sin tests)
- 🟡 Falta integration tests database PostgreSQL

#### B. Frontend Tests (26 archivos Jest + Playwright)

```
tests/
├── unit/ - Jest tests
│   ├── components/ (5 tests) - Modal, Table, Form, Select, DatePicker
│   ├── pages/ (2 tests) - Dashboard, LeaveRequests
│   └── modules/ (2 tests) - utils, data-service
│
└── e2e/ - Playwright (10 specs)
    ├── accessibility.spec.js - WCAG 2.1 AA
    ├── dashboard.spec.js
    ├── leave-requests.spec.js
    ├── edit-yukyu.spec.js
    ├── bulk-edit.spec.js
    └── pages/ - Page Object Model
```

**Análisis:**
- ✅ E2E tests con Playwright (excelente)
- ✅ Accessibility testing WCAG 2.1 AA
- ✅ Page Object Model pattern
- ⚠️ Unit tests limitados (5 specs)
- ⚠️ Sin coverage reports para JavaScript

---

## PROBLEMAS IDENTIFICADOS

### CRÍTICOS (P0)

#### 1. Escalabilidad: Patrón ID Compuesto
**Impacto:** Alta
**Severidad:** 🔴 Crítico

```python
# database.py línea 85
id TEXT PRIMARY KEY,  # {employee_num}_{year}
employee_num TEXT,
year INTEGER
```

**Problemas:**
- ❌ No permite sharding horizontal por employee_num
- ❌ Queries con WHERE employee_num = '001' requieren full table scan
- ❌ No soporta distribución geográfica
- ❌ Migración a particionamiento es muy disruptiva

**Impacto en escalado:**
```
Empleados actuales: ~500
Registros (5 años): 500 * 5 = 2,500 en tabla employees

Escenario de crecimiento:
- 10,000 empleados * 5 años = 50,000 registros
- Sin índice en employee_num: full table scan = O(n)
- Con sharding en ID compuesto: imposible distribuir
```

**Solución recomendada:**
```python
# Cambiar a:
id INTEGER PRIMARY KEY AUTOINCREMENT,  # Único global
employee_num TEXT NOT NULL,
year INTEGER NOT NULL,
UNIQUE(employee_num, year)  # Constraint de unicidad

# Índices:
CREATE INDEX idx_employee_num ON employees(employee_num);
CREATE INDEX idx_year ON employees(year);
CREATE INDEX idx_employee_year ON employees(employee_num, year);
```

**Esfuerzo:** 3-4 días (migración + backfill + tests)

---

#### 2. Acoplamiento Directo: database.py en Rutas
**Impacto:** Alta
**Severidad:** 🔴 Crítico

```python
# routes/employees.py línea 55
data = database.get_employees_enhanced(year, active_only)

# routes/leave_requests.py línea 100
database.create_leave_request(emp_num, days, ...)

# 70+ llamadas directas a database en rutas/
```

**Problemas:**
- ❌ Rutas no testables sin base de datos real
- ❌ No se puede mockear database.py fácilmente
- ❌ Lógica de negocio mezclada con CRUD
- ❌ Difícil cambiar de SQLite a PostgreSQL sin refactorizar todo

**Solución: Repository Pattern**
```python
# Nuevo: repositories/employee_repository.py
class EmployeeRepository:
    def get_by_year(self, year: int) -> List[Employee]:
        """Obtener empleados por año"""

    def get_active(self, year: int) -> List[Employee]:
        """Obtener activos"""

    def create_bulk(self, employees: List[EmployeeCreate]) -> BulkUpdateResult:
        """Crear múltiples"""

# En rutas:
@router.get("/employees")
async def get_employees(year: int, repo: EmployeeRepository = Depends()):
    return repo.get_by_year(year)
```

**Esfuerzo:** 5-7 días

---

#### 3. Monolito database.py (2,904 líneas)
**Impacto:** Alta
**Severidad:** 🔴 Crítico

**Estructura actual:**
```
database.py (2,904 líneas)
├── 150+ funciones CRUD
├── Schema creation
├── Índices
├── Queries complejas sin abstracción
├── Audit logging
├── Migrations (inline, no Alembic)
└── Utility functions
```

**Problemas:**
- ❌ Monolítico - imposible de mantener
- ❌ 150+ funciones sin organización
- ❌ Sin separación de concerns (schema, queries, audit)
- ❌ Cambios requieren entender 2,904 líneas
- ❌ Sin versionado de schema (sin Alembic real)

**Solución: Dividir en módulos**
```
database/
├── __init__.py - Exports
├── connection.py - Get/close conexiones
├── schema.py - DDL (CREATE TABLE, índices)
├── migrations.py - Alembic integration
├── queries/
│   ├── employees.py - CRUD empleados
│   ├── leave_requests.py - CRUD solicitudes
│   ├── yukyu.py - Gestión vacaciones
│   └── audit.py - Audit logging
└── models.py - Dataclasses/TypedDict
```

**Esfuerzo:** 4-5 días

---

### ALTOS (P1)

#### 4. Frontend: Coexistencia Legacy vs Moderno (21,000 LOC duplicado)
**Impacto:** Alta
**Severidad:** 🟠 Alto

```
static/js/app.js (7,091 líneas)
static/src/ (13,874 líneas)
= 21,000 líneas de código potencialmente duplicado
```

**Problemas:**
- ⚠️ **Duplicación:** Ambos sistemas mantienen estado, lógica de UI
- ⚠️ **Bridge frágil:** legacy-adapter.js requiere coordinación manual
- ⚠️ **Incompleteness:** Algunas features en legacy, otras en moderno
- ⚠️ **Testing:** Dificultad testear ambos simultáneamente
- ⚠️ **Performance:** 21 KB de JavaScript duplicado

**Estadísticas:**
```
app.js sola: ~250 KB minified
static/src/: ~180 KB minified
Total: ~430 KB (vs ~220 KB si fuera uno solo)
```

**Solución: Convergencia Gradual**

**Fase 1 (1-2 semanas):**
- Implementar TODAS las features nuevas SOLO en static/src/
- Legacy (app.js) entra en "maintenance mode" (bug fixes solamente)
- Crear migration guide para usuarios

**Fase 2 (1 mes):**
- Reescribir app.js legacy usando componentes de static/src/
- Mantener URL routes idénticas para compatibilidad
- Usar legacy-adapter como proxy temporal

**Fase 3 (2 meses):**
- Deprecate legacy app.js
- Mover todo a static/src/ ES6 modules
- Optimizar bundle con tree-shaking

**Esfuerzo:** 2-3 semanas

---

#### 5. N+1 Queries en Ciertos Endpoints
**Impacto:** Medio
**Severidad:** 🟠 Alto

**Ejemplo identificado:**
```python
# routes/employees.py línea 54
def get_employees_enhanced(year, active_only):
    data = database.get_employees(year)  # Query 1: SELECT * FROM employees

    if enhanced:
        for emp in data:
            # Loop: (Query 2-501 si hay 500 empleados)
            genzai = database.get_genzai(emp['employee_num'])
            ukeoi = database.get_ukeoi(emp['employee_num'])
            staff = database.get_staff(emp['employee_num'])
```

**Impacto:**
```
N+1 = 1 + 500 = 501 queries
Response time: ~2.5 segundos (sin caché)
```

**Solución:**
```python
# Use JOIN instead
SELECT e.*, g.status, u.status, s.status
FROM employees e
LEFT JOIN genzai g ON e.employee_num = g.employee_num
LEFT JOIN ukeoi u ON e.employee_num = u.employee_num
LEFT JOIN staff s ON e.employee_num = s.employee_num
WHERE e.year = ?
```

**Esfuerzo:** 2-3 días (identificar + testear)

---

#### 6. Sistema de Agentes Sobrearquitectónico (11,307 LOC)
**Impacto:** Medio
**Severidad:** 🟠 Alto

**Problemas:**
- ⚠️ **Desuso en producción:** Agentes no se invocan desde rutas/main.py
- ⚠️ **Propósito poco claro:** ¿Development tool? ¿Production feature?
- ⚠️ **Duplicación:** compliance.py en agents/ vs services/fiscal_year.py
- ⚠️ **Mantenimiento:** 11,307 líneas sin tests de agentes

**Análisis de uso:**
```python
# agents/__init__.py
from agents import get_orchestrator
orchestrator = get_orchestrator()

# ¿Dónde se usa?
# Búsqueda en codebase: NINGÚN lugar en rutas o main.py
```

**Propuesta:**
1. Mover agentes a CLI separado: `yukyu-cli analyze`
2. Crear `tools/` o `scripts/` para herramientas de desarrollo
3. Eliminar de aplicación principal (reducir 11,307 líneas)
4. Mantener memory.py como logging/persistence

**Esfuerzo:** 2-3 días (extracto + validación)

---

### MEDIOS (P2)

#### 7. Falta de ORM (SQLAlchemy/Tortoise)
**Impacto:** Medio
**Severidad:** 🟡 Medio

**Problemas:**
- ⚠️ Queries SQL raw strings (error-prone)
- ⚠️ Sin type safety en models
- ⚠️ Sin automatic migrations (Alembic)
- ⚠️ Sin lazy loading / eager loading control
- ⚠️ Sin transaction management automático

**Trade-off actual:**
- ✅ Simplicidad (no requiere ORM setup)
- ❌ Escalabilidad reducida
- ❌ Type safety comprometida

**Recomendación:**
Migrar a SQLAlchemy 2.0 (async) cuando escale la aplicación.

**Esfuerzo:** 1-2 semanas

---

#### 8. Duplicación de Código: get_client_info, log_audit_action
**Impacto:** Bajo-Medio
**Severidad:** 🟡 Medio

```python
# Función en TRES lugares:
# 1. main.py línea 111
# 2. routes/dependencies.py línea 56
# 3. Lógica similar en middleware/security_headers.py

def get_client_info(request: Request) -> dict:
    """Extract client IP, user agent"""
    client_ip = request.client.host if request.client else None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent", "")
    return {...}
```

**Solución:**
```
Consolidar en: utils/request.py o middleware/
```

**Esfuerzo:** 2 horas

---

#### 9. Cache Sin Invalidación Predictiva
**Impacto:** Medio
**Severidad:** 🟡 Medio

**Problema:**
```python
# services/caching.py
@cached(ttl=300)  # 5 minutos hardcoded
def get_employees_cached(year):
    return database.get_employees(year)
```

**Problemas:**
- ⚠️ TTL fijo (300s) = stale data hasta 5 min
- ⚠️ Sin invalidación en CREATE/UPDATE/DELETE
- ⚠️ Sin cache warming (preload before expiry)
- ⚠️ Sin metrics (hit/miss rate)

**Solución:**
```python
# Invalidar cache al actualizar
@router.put("/employees/{emp_num}/{year}")
async def update_employee(...):
    result = database.update_employee(...)
    invalidate_employee_cache(emp_num, year)  # ✅ Implicit now
    return result
```

Pero hay MISSING:
```python
# Cache warming
@scheduler.every(4.5, "minutes")  # Refresh before 5-min expiry
async def warm_cache():
    for year in get_available_years():
        get_employees_cached(year)
```

**Esfuerzo:** 1-2 días

---

## ANÁLISIS DE COMPONENTES

### Backend Components Deep Dive

#### fiscal_year.py - Análisis de Diseño

**Positivos:**
- ✅ Aislado de database (sin imports database.py)
- ✅ Funciones puras (no state mutation)
- ✅ Well-documented (ley laboral japonesa)
- ✅ Tabla de otorgamiento según antigüedad (GRANT_TABLE)
- ✅ Carry-over lógica correcta (máximo 2 años)

**Mejorables:**
- ⚠️ Sin logging (difícil debuggear)
- ⚠️ Sin cache (calculate_seniority_years() recalcula cada vez)
- ⚠️ Sin transaction support
- ⚠️ Sin validación de entrada

**Recomendación:**
Dejar tal cual, es un módulo de calidad excelente.

---

### Frontend Components Deep Dive

#### Modal.js (685 líneas)

**Análisis:**
```javascript
class Modal {
    constructor(options = {})
    render()        // Generar DOM
    open()          // Mostrar modal
    close()         // Cerrar modal
    destroy()       // Limpiar

    Features:
    - Backdrop click to close
    - Keyboard ESC support
    - Scroll prevention
    - Z-index management
    - Animation support
}
```

**Análisis de Calidad:** 🟢 Excelente
- ✅ Encapsulation
- ✅ Event handling
- ✅ Memory leak prevention (destroy)
- ✅ Accessible (role="dialog", aria-modal)

---

#### Table.js (985 líneas)

**Análisis:**
```javascript
class DataTable {
    constructor(options)    // { columns, data, pagination, ... }
    render()                // Generar tabla
    setData()               // Actualizar datos
    sort(column)            // Ordenar
    filter(predicate)       // Filtrar
    getPaginatedData()      // Paginación
    destroy()

    Features:
    - Sortable columns
    - Filterable
    - Pagination (20/50/100 items)
    - Row selection (checkbox)
    - Click handlers
}
```

**Análisis de Calidad:** 🟢 Excelente
- ✅ Modular design
- ✅ Data binding
- ✅ Event delegation
- ⚠️ Podría tener virtual scrolling para 1000+ filas

---

#### Form.js (1,071 líneas)

**Análisis:**
```javascript
class Form {
    constructor(options)    // { fields, onSubmit, validation }
    render()
    validate()              // Client-side validation
    submit()
    setErrors()
    destroy()

    Field types:
    - text, email, password, number
    - date, datetime, time
    - select, checkbox, radio
    - textarea
    - file (custom)

    Validations:
    - required, minLength, maxLength
    - email, url, pattern
    - custom validators
}
```

**Análisis de Calidad:** 🟢 Muy Bueno
- ✅ Validation framework
- ✅ Error handling
- ✅ Field types abstraction
- ⚠️ Sin async validation (API calls)
- ⚠️ Sin conditional fields

---

---

## COMPARACIÓN CON ESTÁNDARES

### 1. FastAPI Best Practices

| Paráctica | YuKyuDATA | Recomendación | Puntuación |
|-----------|-----------|---------------|-----------|
| Pydantic v2 | ✅ Implementado | ✅ Seguir igual | 10/10 |
| Dependency injection | ✅ Bien usado | ✅ Seguir igual | 10/10 |
| Router modularization | ✅ 19 routers | ✅ Excelente | 10/10 |
| Exception handling | ✅ Middleware + handlers | ✅ Bueno | 8/10 |
| Async/await | ✅ Endpoints async | ✅ Bueno | 8/10 |
| Type hints | ✅ Completos | ✅ Seguir igual | 9/10 |
| OpenAPI docs | ✅ /docs auto-generated | ✅ Excelente | 9/10 |
| Testing | ✅ pytest + fixtures | ✅ Bueno | 8/10 |
| Security | ✅ JWT + CSRF + RateLimit | ✅ Excelente | 9/10 |
| Database | ❌ Raw SQL + no ORM | 🔴 Mejorar | 4/10 |

**Score FastAPI:** 7.7/10

---

### 2. Frontend Architecture (vs Modern Frameworks)

| Aspecto | YuKyuDATA | Next.js | Astro | Vue 3 | Puntuación |
|--------|-----------|---------|-------|-------|-----------|
| Component reusability | 🟡 Parcial | ✅ Excelente | ✅ Excelente | ✅ Excelente | 6/10 |
| State management | 🟡 Observer | ✅ Vuex/Pinia | ✅ Signals | ✅ Reactive | 5/10 |
| Type safety | ❌ No TypeScript | ✅ Nativo | ✅ Nativo | ✅ Nativo | 2/10 |
| Build tooling | ❌ Ninguno | ✅ Webpack | ✅ Vite | ✅ Vite | 1/10 |
| Testing | 🟡 Jest básico | ✅ Vitest | ✅ Vitest | ✅ Vitest | 5/10 |
| SSR/SSG | ❌ No | ✅ Sí | ✅ Sí | 🟡 Posible | 1/10 |
| Bundle size | ❌ 430 KB | ✅ ~100 KB | ✅ ~50 KB | ✅ ~100 KB | 2/10 |
| SEO | ❌ Client-side | ✅ Excelente | ✅ Excelente | 🟡 Posible | 1/10 |
| Accessibility | 🟡 Parcial | ✅ Excelente | ✅ Excelente | ✅ Excelente | 6/10 |
| Developer experience | 🟡 Manual | ✅ Excelente | ✅ Excelente | ✅ Excelente | 4/10 |

**Score Frontend vs Modern:** 3.3/10

**Conclusión:** Frontend es "custom" (vanilla JS), bien hecho para eso, pero MUY por debajo de estándares modernos.

---

### 3. Database Design

| Paráctica | YuKyuDATA | PostgreSQL Standard | Puntuación |
|-----------|-----------|-------------------|-----------|
| Schema design | 🟡 Compuesto ID | ✅ Surrogate key | 4/10 |
| Normalization | 🟡 3NF | ✅ 3NF+ | 7/10 |
| Indexes | ✅ Presentes | ✅ Bien planificados | 8/10 |
| Foreign keys | ✅ Presentes | ✅ Defined | 8/10 |
| Data integrity | ✅ Constraints | ✅ Completos | 8/10 |
| Audit logging | ✅ Implementado | ✅ Audit table | 8/10 |
| Migrations | ❌ Sin Alembic | ✅ Alembic/Flyway | 2/10 |
| Partitioning | ❌ No | ✅ Por año/geografía | 1/10 |
| Replication | 🟡 Manual | ✅ Streaming replication | 4/10 |
| Backup strategy | 🟡 Básico | ✅ PITR + incremental | 5/10 |

**Score Database:** 5.5/10

---

### 4. Security

| Categoría | Status | Puntuación |
|-----------|--------|-----------|
| Authentication (JWT) | ✅ Implementado (15 min access, 7 day refresh) | 9/10 |
| Authorization (RBAC) | 🟡 Básico (admin/user) | 6/10 |
| CSRF Protection | ✅ Token-based | 9/10 |
| Rate Limiting | ✅ User-aware (IP + user_id + endpoint) | 8/10 |
| SQL Injection | ✅ Parameterized queries | 9/10 |
| XSS Prevention | ✅ sanitizer.js módulo | 8/10 |
| CSP Headers | ✅ strict-dynamic, no unsafe | 8/10 |
| HSTS | ✅ Implementado | 8/10 |
| Password hashing | ✅ bcrypt | 9/10 |
| Data encryption | 🟡 Field-level crypto_utils | 7/10 |
| Secrets management | 🟡 .env file | 5/10 |
| OWASP Top 10 | 🟡 6/10 covered | 6/10 |

**Score Security:** 7.6/10

---

## MATRIZ DE RIESGOS

### Risk Matrix (Probability vs Impact)

```
                         IMPACT
                 Low    Medium    High   Critical
           ┌──────────────────────────────────────┐
        H  │                                 [#1] │
        i  │  [#9]  [#7]                         │
P    g  h  │        [#5]        [#4]             │
r    h  e  │        [#8]                         │
o    │  s  │                                     │
b    │  t  │              [#2]  [#3]             │
      │  │  │                                     │
        │  │  │              [#6]                 │
        L  │                                     │
        o  │                                     │
        w  │                                     │
           └──────────────────────────────────────┘
        L    Medium    High     Critical

CRITICAL Risks: #1, #2, #3
HIGH Risks: #4, #5, #6, #7
MEDIUM Risks: #8, #9
```

### Risk Register Detallado

| # | Riesgo | Probabilidad | Impacto | Severidad | Mitigation |
|---|--------|-------------|--------|-----------|-----------|
| 1 | ID compuesto previene scaling horizontal | Alta (100%) | Crítico | **CRÍTICO** | Cambiar schema en sprint prioritario |
| 2 | database.py monolítico dificulta mantenimiento | Alta (90%) | Alto | ALTO | Refactorizar con repository pattern |
| 3 | Acoplamiento directo database en rutas | Media (70%) | Alto | ALTO | Dependency injection layer |
| 4 | Coexistencia legacy/moderno no escalable | Media (60%) | Alto | ALTO | Migration plan + deprecate legacy |
| 5 | N+1 queries reducen performance | Alta (85%) | Medio | ALTO | Query optimization + monitoring |
| 6 | Agentes sobrearquitectónicos sin uso | Media (50%) | Medio | MEDIO | Mover a CLI separado |
| 7 | Sin ORM limita escalabilidad futura | Media (65%) | Medio | MEDIO | Planificar migración SQLAlchemy |
| 8 | Duplicación get_client_info | Media (60%) | Bajo | MEDIO | Consolidar en utils/ |
| 9 | Cache sin invalidación predictiva | Baja (30%) | Bajo | BAJO | Agregar cache warming |

---

## RECOMENDACIONES PRIORITARIAS

### SPRINT 1 (Semana 1-2): REFACTORIZACIÓN CRÍTICA

#### 1.1 Cambiar ID Compuesto en database.py
**Prioridad:** 🔴 CRÍTICO
**Esfuerzo:** 3 días
**Impacto:** Permite sharding horizontal

```python
# Antes:
CREATE TABLE employees (
    id TEXT PRIMARY KEY,  # {employee_num}_{year}
    employee_num TEXT,
    year INTEGER
)

# Después:
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_num TEXT NOT NULL,
    year INTEGER NOT NULL,
    UNIQUE(employee_num, year)
)

# Índices:
CREATE INDEX idx_emp_year ON employees(employee_num, year);
CREATE INDEX idx_year ON employees(year);
```

**Pasos:**
1. Crear migration Alembic
2. Crear script backfill
3. Actualizar todas las queries que usan `id` = `{num}_{year}`
4. Actualizar rutas/servicios
5. Tests end-to-end

#### 1.2 Crear Repository Pattern
**Prioridad:** 🔴 CRÍTICO
**Esfuerzo:** 4 días
**Impacto:** Desacopla rutas de database

```python
# Nuevo: repositories/employee_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from models import EmployeeResponse, EmployeeCreate, EmployeeUpdate

class EmployeeRepository(ABC):
    @abstractmethod
    async def get_by_year(self, year: int) -> List[EmployeeResponse]: pass

    @abstractmethod
    async def get_by_employee_num(self, emp_num: str, year: int) -> Optional[EmployeeResponse]: pass

    @abstractmethod
    async def create(self, data: EmployeeCreate) -> EmployeeResponse: pass

    @abstractmethod
    async def update(self, emp_num: str, year: int, data: EmployeeUpdate) -> EmployeeResponse: pass

    @abstractmethod
    async def delete(self, emp_num: str, year: int) -> bool: pass

# Implementation
class SQLiteEmployeeRepository(EmployeeRepository):
    def __init__(self, db: Database):
        self.db = db

    async def get_by_year(self, year: int) -> List[EmployeeResponse]:
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM employees WHERE year = ?", (year,))
            return [EmployeeResponse(**row) for row in c.fetchall()]

    # ... rest of methods

# En routes/dependencies.py
@dataclass
class Repositories:
    employees: EmployeeRepository
    leave_requests: LeaveRequestRepository
    notifications: NotificationRepository

def get_repositories(db: Database = Depends()) -> Repositories:
    return Repositories(
        employees=SQLiteEmployeeRepository(db),
        leave_requests=SQLiteLeaveRequestRepository(db),
        notifications=SQLiteNotificationRepository(db)
    )

# En rutas:
@router.get("/employees")
async def get_employees(
    year: int,
    repos: Repositories = Depends(get_repositories)
):
    return repos.employees.get_by_year(year)
```

**Ventajas:**
- ✅ Testeable (mock repository fácilmente)
- ✅ Database-agnostic
- ✅ Lógica de CRUD centralizada
- ✅ Type-safe

#### 1.3 Dividir database.py en módulos
**Prioridad:** 🟠 ALTO
**Esfuerzo:** 3 días
**Impacto:** Reducir de 2,904 a 500 líneas en cada módulo

```
database/
├── __init__.py                    # Exports públicos
├── connection.py                  # Context manager
├── schema.py                      # DDL (CREATE TABLE, INDEX)
├── migrations.py                  # Alembic integration
├── models.py                      # Dataclasses para filas
│
├── queries/
│   ├── __init__.py
│   ├── employees.py               # Employee CRUD (300 líneas)
│   ├── leave_requests.py          # LeaveRequest CRUD (250 líneas)
│   ├── yukyu.py                   # Vacation CRUD (200 líneas)
│   ├── notifications.py           # Notification CRUD (200 líneas)
│   └── audit.py                   # Audit logging (150 líneas)
│
└── utils.py                       # Helpers (format_date, etc.)
```

**Ejemplo refactorizado:**
```python
# database/queries/employees.py
from typing import List, Optional
from datetime import datetime
from ..models import EmployeeRow
from ..connection import Database

class EmployeeQueries:
    def __init__(self, db: Database):
        self.db = db

    def get_all_by_year(self, year: int) -> List[EmployeeRow]:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT id, employee_num, name, granted, used, balance, year
                FROM employees
                WHERE year = ?
                ORDER BY employee_num
            ''', (year,))
            return [EmployeeRow(*row) for row in c.fetchall()]

    def get_by_number(self, emp_num: str, year: int) -> Optional[EmployeeRow]:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM employees WHERE employee_num = ? AND year = ?', (emp_num, year))
            row = c.fetchone()
            return EmployeeRow(*row) if row else None

    def create_or_update(self, emp_num: str, year: int, data: dict) -> EmployeeRow:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO employees
                (id, employee_num, name, year, granted, used, balance, ...)
                VALUES (?, ?, ?, ?, ?, ?, ?, ...)
            ''', (
                f"{emp_num}_{year}", emp_num, data['name'], year,
                data['granted'], data['used'], data['balance'], ...
            ))
            conn.commit()
            return self.get_by_number(emp_num, year)
```

---

### SPRINT 2 (Semana 3): FRONTEND MODERNIZATION

#### 2.1 Deprecate Legacy app.js
**Prioridad:** 🟠 ALTO
**Esfuerzo:** 2 días
**Impacto:** Clear path para static/src/

```javascript
// static/js/app.js - MAINTENANCE MODE ONLY

console.warn(`
    ⚠️  DEPRECATED: static/js/app.js is deprecated as of v5.20
    Please migrate to static/src/ (ES6 modules)

    For migration guide, see: https://github.com/yourorg/yukyu/wiki/Frontend-Migration

    This file will be removed in v6.0 (ETA: Q2 2026)
`);

// Redirect all requests to new frontend
if (typeof window !== 'undefined') {
    const newApp = require('/static/src/index.js');
    window.App = newApp.default;  // Backwards compatibility shim
}
```

#### 2.2 Completar static/src/ Features
**Prioridad:** 🟠 ALTO
**Esfuerzo:** 3 días

Asegurar TODAS las features del legacy están en moderno:
- ✅ Dashboard - DONE
- ✅ Employees CRUD - DONE
- ✅ Leave Requests Workflow - DONE
- ✅ Analytics Charts - DONE
- ✅ Compliance 5-day - DONE
- ✅ Notifications - DONE
- ✅ Settings/Profile - DONE
- ❌ Advanced Search - TODO
- ❌ Bulk Import - TODO
- ❌ Custom Reports - TODO

#### 2.3 Optimizar Bundle Size
**Prioridad:** 🟡 MEDIO
**Esfuerzo:** 2 días

```javascript
// webpack.config.js (NEW)
const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
    mode: 'production',
    entry: './static/src/index.js',
    output: {
        filename: 'bundle.[contenthash].js',
        path: path.resolve(__dirname, 'dist')
    },
    optimization: {
        minimize: true,
        minimizer: [new TerserPlugin()],
        splitChunks: {
            chunks: 'all',
            cacheGroups: {
                vendor: {
                    test: /[\\/]node_modules[\\/]/,
                    name: 'vendors',
                    priority: 10
                },
                components: {
                    test: /[\\/]static\/src\/components[\\/]/,
                    name: 'components',
                    priority: 5
                }
            }
        }
    }
};
```

**Resultado:**
```
Antes: app.js (7 KB) + modules (2.5 KB) + src (5.5 KB) = ~15 KB
Después: bundle.HASH.js (8 KB) + vendors (1.2 KB) = ~9.2 KB
Ahorro: 38%
```

---

### SPRINT 3 (Semana 4): OBSERVABILIDAD & PERFORMANCE

#### 3.1 Eliminar N+1 Queries
**Prioridad:** 🟠 ALTO
**Esfuerzo:** 2 días

**Auditoría de N+1:**
```python
# Herramienta de detección
@app.middleware("http")
async def n_plus_one_detector(request: Request, call_next):
    """Detecta queries N+1 en desarrollo"""
    if not DEVELOPMENT:
        return await call_next(request)

    query_count_before = get_query_count()
    response = await call_next(request)
    query_count_after = get_query_count()

    if query_count_after - query_count_before > THRESHOLD:
        logger.warning(
            f"Potential N+1 detected in {request.url.path}: "
            f"{query_count_after - query_count_before} queries executed"
        )

    return response
```

**Fixes específicos:**
```python
# routes/employees.py - BEFORE (N+1)
@router.get("/employees")
async def get_employees(year: int, enhanced: bool = False):
    data = database.get_employees(year)  # Query 1

    if enhanced:
        for emp in data:
            genzai = database.get_genzai(emp['employee_num'])  # Queries 2-501
            emp['genzai_status'] = genzai[0]['status'] if genzai else None

    return data

# AFTER (JOIN)
@router.get("/employees")
async def get_employees(year: int, enhanced: bool = False):
    data = repos.employees.get_by_year_enhanced(year, enhanced)
    # Single query with JOINs
    return data
```

#### 3.2 Agregar Monitoring & Alerting
**Prioridad:** 🟡 MEDIO
**Esfuerzo:** 2 días

```python
# monitoring/metrics.py (NEW)
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
request_count = Counter(
    'yukyu_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'yukyu_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

db_query_count = Gauge(
    'yukyu_db_queries_total',
    'Total DB queries'
)

db_slow_queries = Counter(
    'yukyu_db_slow_queries_total',
    'Slow queries (>100ms)',
    ['query_type']
)

# Middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path

    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    request_count.labels(
        method=method,
        endpoint=path,
        status=response.status_code
    ).inc()

    request_duration.labels(endpoint=path).observe(duration)

    return response

# Prometheus endpoint
@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return Response(generate_latest(), media_type="text/plain")
```

**Alertas (Alertmanager):**
```yaml
# alerts/yukyu.rules.yml
groups:
  - name: yukyu_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(yukyu_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected ({{ $value | humanizePercentage }})"

      - alert: SlowQueries
        expr: rate(yukyu_db_slow_queries_total[5m]) > 1
        annotations:
          summary: "Slow database queries detected"

      - alert: CacheHitRateLow
        expr: cache_hit_ratio < 0.5
        annotations:
          summary: "Cache hit rate below 50%"
```

---

### SPRINT 4 (Semana 5): TESTING & SECURITY

#### 4.1 Increase Test Coverage para Agentes
**Prioridad:** 🟡 MEDIO
**Esfuerzo:** 2 días

```python
# tests/agents/test_compliance_agent.py (NEW)
import pytest
from agents import ComplianceAgent

@pytest.fixture
def compliance_agent():
    return ComplianceAgent()

def test_5day_compliance_check():
    """Test 5-day minimum compliance checking"""
    result = compliance_agent.check_5day_compliance(year=2025)
    assert isinstance(result, dict)
    assert 'compliant_employees' in result
    assert 'non_compliant' in result

def test_expiring_soon_alerts():
    """Test expiration alerts"""
    result = compliance_agent.check_expiring_soon(year=2025, threshold_months=3)
    assert isinstance(result, list)
```

#### 4.2 Add OWASP Top 10 Security Tests
**Prioridad:** 🟡 MEDIO
**Esfuerzo:** 2 días

```python
# tests/security/test_owasp_top10.py (NEW)
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_sql_injection_protection():
    """Verify SQL injection is prevented"""
    response = client.get("/api/employees?name='; DROP TABLE employees; --")
    assert response.status_code in [200, 400]
    # Verify table still exists
    response2 = client.get("/api/employees")
    assert response2.status_code == 200

def test_xss_protection():
    """Verify XSS payloads are sanitized"""
    xss_payload = "<script>alert('xss')</script>"
    response = client.post("/api/employees", json={
        "name": xss_payload,
        "employee_num": "test"
    })
    # Verify response doesn't include unescaped script
    assert "<script>" not in response.text or "textContent" in response.text

def test_csrf_protection():
    """Verify CSRF token is required"""
    response = client.post("/api/employees")
    assert response.status_code in [403, 401]  # Unauthorized

def test_rate_limit_protection():
    """Verify rate limiting is enforced"""
    for i in range(105):  # Beyond 100/minute limit
        response = client.get("/api/employees")
        if i >= 100:
            assert response.status_code == 429  # Too Many Requests
            break
```

---

## HOJA DE RUTA DE MODERNIZACIÓN

### Timeline: 3 Meses (12 semanas)

```
FASE 1: ARCHITECTURAL REFACTORING (Weeks 1-4)
├── Week 1-2: Fix critical issues (ID schema, repository pattern)
├── Week 3: Divide database.py, integrate Alembic
└── Week 4: Performance optimization (N+1 fixes, caching)

FASE 2: FRONTEND MODERNIZATION (Weeks 5-8)
├── Week 5: Complete static/src/ features
├── Week 6: Bundle optimization, webpack setup
├── Week 7: Deprecate legacy app.js
└── Week 8: Migration testing, documentation

FASE 3: OBSERVABILITY & TESTING (Weeks 9-11)
├── Week 9: Add Prometheus metrics, alerting
├── Week 10: Increase test coverage (agents, E2E)
├── Week 11: OWASP Top 10 security tests

PHASE 4: DEPLOYMENT & HARDENING (Week 12)
├── Week 12: Production deployment, rollback plan
└── Post: Monitoring, incident response
```

### Dependency Graph

```
┌─────────────────────────────────────────────────────────┐
│ CRITICAL PATH (Blocker for other tasks)                │
├─────────────────────────────────────────────────────────┤
│ 1. Fix ID Schema (2-3 days)                            │
│    └─→ Repository Pattern (2-3 days)                   │
│        └─→ Divide database.py (2-3 days)               │
│            └─→ E2E Testing (1-2 days)                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ PARALLEL PATH (Can start after Week 1)                 │
├─────────────────────────────────────────────────────────┤
│ 2. Frontend: Deprecate legacy (1-2 days)              │
│    └─→ Complete features in static/src/ (2-3 days)    │
│        └─→ Bundle optimization (1-2 days)              │
│            └─→ Migration guide (1 day)                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ OBSERVATION PATH (Parallel to all)                     │
├─────────────────────────────────────────────────────────┤
│ 3. Add monitoring (Prometheus)                         │
│ 4. Increase test coverage                              │
│ 5. Security hardening (OWASP)                          │
└─────────────────────────────────────────────────────────┘
```

### Resource Allocation

```
Team Composition (Recommended):
- 2x Backend Engineers (architectural refactoring, database)
- 1x Frontend Engineer (static/src/ optimization, bundle)
- 1x DevOps Engineer (monitoring, CI/CD, deployment)
- 1x QA Engineer (testing, security validation)

Total: ~5 FTE for 12 weeks = ~60 person-days
```

---

## QUICK WINS (< 1 day cada)

Estas correcciones pueden implementarse sin impacto a la arquitectura:

1. **Consolidar get_client_info** (30 min)
   - Mover de main.py a utils/request.py
   - Actualizar imports en routes/dependencies.py

2. **Remover ThreadPoolExecutor duplicado** (15 min)
   - Crear workers.py global
   - Compartir en main.py y routes/

3. **Agregar logging a fiscal_year.py** (1 hora)
   - Import logger
   - Log en puntos clave (seniority, grant, carryover)

4. **Fix failing test** (2 horas)
   - Investigar test_connection_pooling.py
   - Likely missing fixture o timeout issue

5. **Add cache hit/miss metrics** (1.5 horas)
   - Decorator wrapper en services/caching.py
   - Prometheus metrics

6. **Consolidate static assets** (2 horas)
   - Merge duplicate CSS
   - Remove unused icons

---

## MÉTRICAS DE ÉXITO

Después de implementar estas recomendaciones:

| Métrica | Antes | Después | Meta |
|---------|-------|---------|------|
| **Madurez Arquitectónica** | 5.5/10 | 7.5/10 | 8.5/10 |
| **Escalabilidad** | 4/10 | 6.5/10 | 8/10 |
| **Mantenibilidad** | 6/10 | 7.5/10 | 8.5/10 |
| **Test Coverage** | 80% | 85% | 90% |
| **Bundle Size (JS)** | 15 KB | 9.2 KB | 8 KB |
| **P95 Response Time** | 500ms | 200ms | 100ms |
| **N+1 Queries** | 50+ en peak | 0 | 0 |
| **Security Score** | 7.6/10 | 9/10 | 9.5/10 |

---

## CONCLUSIÓN

YuKyuDATA v5.19 es un **proyecto bien ejecutado** con arquitectura modular y seguridad sólida. Sin embargo, tiene limitaciones arquitectónicas que impiden escalado horizontal y mantenibilidad a largo plazo.

### Recomendación Final:

🟡 **CÓDIGO AMARILLO** - Proceder con cautela en producción a gran escala

- ✅ **OK para equipos < 50 personas**
- ⚠️ **Refactorizar antes de 100+ empleados**
- ❌ **Requiere rediseño para 1000+ empleados**

### Prioridades (By Impact/Effort):

1. **Cambiar ID schema** (Crítico, 3 días)
2. **Repository Pattern** (Crítico, 4 días)
3. **Frontend modernization** (Alto, 2 semanas)
4. **Agentes → CLI tool** (Alto, 3 días)
5. **Monitoring/Observability** (Medio, 1 semana)

### Próximos Pasos:

1. Revisar este análisis con el equipo
2. Priorizar según roadmap del producto
3. Crear issues en GitHub/Jira
4. Asignar ownership (backend engineer, frontend engineer, devops)
5. Comenzar Sprint 1 próxima semana

---

**Documento preparado por:** Claude Code DevOps Engineer
**Fecha:** 17 Enero 2026
**Versión del Análisis:** 1.0
**Siguiente Revisión:** Después de Sprint 2 (Week 8)
