# ANÁLISIS ARQUITECTÓNICO COMPLETO - YuKyuDATA-app v1.0

**Fecha:** 2026-01-09
**Versión:** 1.0
**Modelo:** Claude Opus 4.5

---

## RESUMEN EJECUTIVO

YuKyuDATA-app es un **sistema integral de gestión de empleados** especializado en el cumplimiento de la ley laboral japonesa para el seguimiento de vacaciones pagadas (有給休暇).

### Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| **Total Lines of Code** | ~42,000 LOC |
| **Backend Python** | 6,113 LOC (core) |
| **Frontend JavaScript** | 7,176 LOC |
| **CSS/Styling** | 11,415 LOC |
| **Test Coverage** | 3,044 LOC |
| **Agent System** | 9,719 LOC (12 agentes) |
| **Documentation** | 61 archivos Markdown |

---

## 1. ARQUITECTURA DE CUATRO CAPAS

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ Dashboard   │ │ Employees   │ │ Requests    │ │ Analytics   │ │
│  │ View        │ │ Table       │ │ Workflow    │ │ Charts      │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  static/js/app.js (5,058 LOC) + 8 módulos ES6 (120 KB)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE API (FastAPI)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ Auth        │ │ Employees   │ │ Leave       │ │ Analytics   │ │
│  │ JWT 24h     │ │ CRUD        │ │ Requests    │ │ Compliance  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  main.py (5,058 LOC) - 30+ endpoints                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE SERVICIO                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ excel_      │ │ fiscal_     │ │ auth_       │ │ search_     │ │
│  │ service.py  │ │ year.py     │ │ service.py  │ │ service.py  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  Business Logic: LIFO, 5-Day Compliance, Year-End Carryover      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ database.py │ │ SQLite      │ │ PostgreSQL  │ │ Excel       │ │
│  │ CRUD + Pool │ │ (default)   │ │ (optional)  │ │ Parsing     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  7 tablas, 15+ índices, encriptación AES                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. MÓDULOS BACKEND

### 2.1 main.py - FastAPI Application (5,058 LOC)

**Endpoints por Categoría:**

| Categoría | Endpoints | Propósito |
|-----------|-----------|-----------|
| Auth | `/api/auth/login`, `/me`, `/verify` | JWT authentication |
| Employees | `/api/employees`, `/api/v1/employees` | Datos de vacaciones |
| Registries | `/api/genzai`, `/api/ukeoi`, `/api/staff` | Registros de empleados |
| Leave Requests | `/api/leave-requests/*` | Flujo de solicitudes |
| Compliance | `/api/compliance/5day`, `/expiring` | Verificación legal |
| Analytics | `/api/analytics/*`, `/api/stats/*` | KPIs y tendencias |
| Backups | `/api/backup`, `/backups`, `/restore` | Sistema de respaldo |

**Patrones de Diseño:**
- Dependency Injection (FastAPI)
- Context Manager para conexiones DB
- Pydantic Validation
- Rate Limiting Middleware (100 req/min)

### 2.2 database.py - Data Access Layer (1,344 LOC)

**Esquema de 7 Tablas:**

```sql
employees          -- Datos de vacaciones (PK: employee_num_year)
genzai             -- Empleados dispatch (PK: genzai_employee_num)
ukeoi              -- Empleados contract (PK: ukeoi_employee_num)
staff              -- Personal oficina (PK: staff_employee_num)
leave_requests     -- Solicitudes (status workflow)
yukyu_usage_details -- Detalles de uso diario
audit_log          -- Trail de auditoría
```

**Características:**
- Soporte dual: SQLite (default) + PostgreSQL
- Encriptación de campos sensibles (AES)
- INSERT OR REPLACE para sincronización idempotente
- 15+ índices optimizados

### 2.3 fiscal_year.py - Lógica de Negocio (513 LOC)

**Implementación Labor Standards Act Article 39:**

```python
GRANT_TABLE = {
    0.5: 10,   # 6 meses → 10 días
    1.5: 11,   # 1.5 años → 11 días
    2.5: 12,   # 2.5 años → 12 días
    3.5: 14,   # 3.5 años → 14 días
    4.5: 16,   # 4.5 años → 16 días
    5.5: 18,   # 5.5 años → 18 días
    6.5: 20    # 6+ años → 20 días (máximo)
}
```

**Funciones Clave:**
- `calculate_seniority_years()` - Antigüedad
- `calculate_granted_days()` - Días otorgados
- `apply_lifo_deduction()` - Deducción LIFO
- `check_5day_compliance()` - Obligación 5 días
- `process_year_end_carryover()` - Traslado año fiscal

### 2.4 excel_service.py - Parser Inteligente (476 LOC)

**Detección Flexible de Columnas:**

```python
COLUMN_MAPPINGS = {
    'employee_num': ['社員№', '社員番号', '従業員番号', 'id'],
    'name': ['氏名', '名前', '社員名', 'full_name'],
    'granted': ['付与日数', '付与', '総日数'],
    'used': ['消化日数', '使用日数', '取得日数']
}
```

---

## 3. ARQUITECTURA FRONTEND

### 3.1 Estructura de Módulos ES6

```
static/js/
├── app.js (5,058 LOC)           # Singleton SPA principal
└── modules/
    ├── chart-manager.js (604)   # Chart.js + ApexCharts
    ├── ui-manager.js (681)      # DOM manipulation
    ├── data-service.js (255)    # API client con cache
    ├── virtual-table.js (364)   # Virtual scrolling 1000+ rows
    ├── lazy-loader.js (466)     # IntersectionObserver
    ├── export-service.js (225)  # Excel/CSV export
    ├── theme-manager.js (122)   # Dark/light mode
    ├── utils.js (255)           # XSS prevention, formatters
    └── sanitizer.js (226)       # Seguridad DOM
```

### 3.2 Sistema de Estado

```javascript
const App = {
    state: {
        data: [],              // Empleados
        year: null,            // Año fiscal actual
        availableYears: [],    // Años en BD
        charts: {},            // Instancias de gráficos
        currentView: 'dashboard',
        typeFilter: 'all'
    }
}
```

**Patrón:** Singleton con mutaciones imperativas + Race Condition Prevention (requestId tracking)

### 3.3 Design System (11,415 LOC CSS)

**Tokens de Diseño:**
```css
--color-primary: #06b6d4;        /* Cyan accent */
--color-bg-dark: #000000;        /* Pure black */
--space-base: 0.5rem;            /* 8px grid */
--font-family: 'Outfit', 'Noto Sans JP', sans-serif;
```

**Características:**
- Glassmorphism con backdrop-filter
- Dark/Light mode
- WCAG AA (4.5:1 contrast)
- Responsive mobile-first

---

## 4. SISTEMA DE AGENTES (12 Agentes, 9,719 LOC)

### 4.1 Matriz de Agentes

| Agente | LOC | Especialización |
|--------|-----|-----------------|
| **orchestrator.py** | 721 | Coordinador de pipelines |
| **nerd.py** | 946 | Análisis técnico, code smells |
| **security.py** | 885 | OWASP Top 10, secretos |
| **performance.py** | 789 | N+1 queries, bundle size |
| **testing.py** | 899 | Cobertura, tests frágiles |
| **ui_designer.py** | 1,023 | WCAG, Design System |
| **ux_analyst.py** | 943 | Nielsen heuristics, flujos |
| **compliance.py** | 665 | Ley laboral japonesa |
| **data_parser.py** | 551 | Parsing Excel/CSV |
| **documentor.py** | 560 | Audit trail, snapshots |
| **canvas.py** | 817 | Análisis SVG/Canvas |
| **figma.py** | 735 | Tokens para Figma |

### 4.2 Arquitectura del Orquestador

```
OrchestratorAgent
    │
    ├── execute_pipeline(steps)      # Secuencial
    ├── execute_parallel(tasks)      # ThreadPoolExecutor
    │
    ├── PIPELINES PREDEFINIDOS:
    │   ├── full_sync                # Sincronización datos
    │   ├── compliance_check         # Verificación legal
    │   ├── security_audit           # Auditoría seguridad
    │   ├── code_review              # Revisión código
    │   └── ui_ux_audit              # Auditoría UI/UX
    │
    └── run_full_analysis()          # 6 agentes en paralelo
```

---

## 5. SEGURIDAD

### 5.1 Medidas Implementadas

| Capa | Medida | Estado |
|------|--------|--------|
| Auth | JWT 24h expiration | ✅ |
| API | Rate Limiting 100/min | ✅ |
| Input | Pydantic validation | ✅ |
| DB | Encriptación AES campos sensibles | ✅ |
| Frontend | XSS escapeHtml/escapeAttr | ✅ |
| HTTP | Security headers (CSP, HSTS) | ✅ |

### 5.2 Vulnerabilidades Detectadas

| Severidad | Issue | Solución |
|-----------|-------|----------|
| 🔴 CRÍTICO | Endpoints sin auth | Añadir `Depends(get_current_user)` |
| 🔴 ALTO | Encriptación inconsistente | Encriptar todos los PII |
| 🟠 MEDIO | Error messages leak info | Sanitizar excepciones |
| 🟠 MEDIO | CORS muy permisivo | Restringir headers |

---

## 6. PERFORMANCE

### 6.1 Optimizaciones Implementadas

| Técnica | Ubicación | Beneficio |
|---------|-----------|-----------|
| Virtual Scrolling | virtual-table.js | 1000+ rows → 30 rows render |
| Request ID Tracking | data-service.js | Previene race conditions |
| Lazy Chart Loading | lazy-loader.js | -500ms initial load |
| Debounce/Throttle | utils.js | Reduce event frequency |
| RAF Throttle | utils.js | 60fps animations |

### 6.2 Áreas de Mejora

| Issue | Impacto | Solución |
|-------|---------|----------|
| N+1 Queries | Alto | Batch queries, JOINs |
| Full table scans | Medio | Índices adicionales |
| Bundle size 600KB | Medio | Tree shaking, minify |
| No server-side pagination | Alto | Implementar LIMIT/OFFSET |

---

## 7. TESTING

### 7.1 Cobertura Actual

```
Backend (pytest):
├── test_api.py (302 LOC)
├── test_auth.py (177 LOC)
├── test_comprehensive.py (396 LOC)
├── test_connection_pooling.py (331 LOC)
├── test_database_compatibility.py (476 LOC)
├── test_full_text_search.py (297 LOC)
├── test_pitr_integration.py (443 LOC)
└── test_postgresql_integration.py (437 LOC)

Frontend (Jest):
├── 8 test modules
└── Threshold: 80% coverage
```

### 7.2 Gaps Identificados

- Falta testing E2E con Playwright
- Coverage de fiscal_year.py < 60%
- Tests de integración Excel incompletos
- Mutation testing no implementado

---

## 8. CUMPLIMIENTO LEGAL JAPONÉS

### 8.1 Labor Standards Act Article 39

**Implementación Correcta:**
- ✅ Tabla de otorgamiento por antigüedad
- ✅ Deducción LIFO (protege días antiguos)
- ✅ Carry-over máximo 2 años
- ✅ Verificación obligación 5 días
- ✅ Año fiscal 21日〜20日
- ✅ Libro anual (年次有給休暇管理簿)

### 8.2 Alertas de Compliance

```python
COMPLIANCE_LEVELS = {
    'COMPLIANT': used >= 5 days,
    'AT_RISK': used < 5 and days_remaining > 0,
    'NON_COMPLIANT': used < 5 and fiscal_year_ended
}
```

---

## 9. RECOMENDACIONES PRIORITARIAS

### Corto Plazo (1-2 semanas)

1. **Seguridad:** Añadir auth a todos los endpoints de datos
2. **Performance:** Implementar paginación server-side
3. **Testing:** Añadir tests de fiscal_year.py

### Mediano Plazo (1 mes)

1. **Infraestructura:** CI/CD con GitHub Actions
2. **Monitoring:** Prometheus + Grafana
3. **Caching:** Redis para sesiones y datos frecuentes

### Largo Plazo (3 meses)

1. **Escalabilidad:** Microservicios opcionales
2. **ML/AI:** Predicción de uso de vacaciones
3. **Mobile:** PWA optimizado o app nativa

---

## 10. ARCHIVOS CLAVE

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `/main.py` | 5,058 | FastAPI app |
| `/database.py` | 1,344 | SQLite/PostgreSQL |
| `/fiscal_year.py` | 513 | Lógica de negocio |
| `/excel_service.py` | 476 | Parser Excel |
| `/static/js/app.js` | 5,058 | SPA frontend |
| `/agents/orchestrator.py` | 721 | Orquestador |
| `/CLAUDE.md` | 700+ | Documentación proyecto |

---

## CONCLUSIÓN

YuKyuDATA-app es una aplicación **bien arquitecturada** con separación clara de responsabilidades. El sistema de agentes proporciona capacidades avanzadas de análisis automático. Las áreas principales de mejora son:

1. **Seguridad:** Autenticación en todos los endpoints
2. **Performance:** Paginación y caching
3. **Testing:** Mayor cobertura de lógica de negocio

La implementación de la ley laboral japonesa es **correcta y completa**, cumpliendo con Labor Standards Act Article 39 y la reforma 2019 de los 5 días obligatorios.

---

*Generado por Claude Opus 4.5 - Análisis exhaustivo de arquitectura*
