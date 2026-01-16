# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Hablame en castellano por favor.

> **IMPORTANTE**: Lee también `CLAUDE_MEMORY.md` para contexto de sesiones anteriores, decisiones de arquitectura, errores conocidos y features ya implementadas.

---

## Project Overview

**YuKyuDATA-app** es un sistema de gestión de empleados especializado en cumplimiento de la ley laboral japonesa para vacaciones pagadas (有給休暇).

**Tech Stack:** FastAPI + SQLite + Vanilla JavaScript (ES6 modules) + Chart.js

**Data Sources:**
- `有給休暇管理.xlsm` - Master de vacaciones
- `【新】社員台帳(UNS)T　2022.04.05～.xlsm` - Registro de empleados (hojas: DBGenzaiX, DBUkeoiX, DBStaffX)

---

## Development Commands

```bash
# Iniciar servidor con auto-reload
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Iniciar con puerto dinámico (recomendado en Windows)
script\start_app_dynamic.bat

# Tests backend
pytest tests/ -v
pytest tests/test_api.py::test_sync_employees  # test individual

# Tests frontend
npx jest
npx jest --watch

# Dependencias
pip install fastapi uvicorn openpyxl python-multipart pydantic PyJWT python-dotenv XlsxWriter
npm install
```

---

## Architecture

```
API Layer (main.py)              ← FastAPI endpoints, JWT auth
    ↓
Service Layer                    ← excel_service.py (parsing), fiscal_year.py (business logic)
    ↓
Data Layer (database.py)         ← SQLite CRUD operations
    ↓
Database (yukyu.db)              ← 7 tablas con 15+ índices
```

### Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `main.py` | FastAPI app con ~30 endpoints |
| `database.py` | SQLite CRUD, sistema de backups |
| `excel_service.py` | Parsing inteligente de Excel |
| `fiscal_year.py` | **CRÍTICO** - Lógica de ley laboral japonesa |
| `static/js/app.js` | SPA principal |
| `static/js/modules/` | 8 módulos ES6 |

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

- `employees` - Datos de vacaciones (múltiples registros por empleado por año)
- `genzai` - Empleados de despacho (派遣社員)
- `ukeoi` - Empleados contratistas (請負社員)
- `staff` - Personal de oficina
- `leave_requests` - Solicitudes (workflow: PENDING → APPROVED/REJECTED)
- `yukyu_usage_details` - Fechas individuales de uso

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

- `data-service.js` - Cliente API con cache 5 min
- `chart-manager.js` - Chart.js + ApexCharts
- `ui-manager.js` - DOM manipulation
- `virtual-table.js` - Virtual scrolling para 1000+ filas
- `utils.js` - XSS prevention: `escapeHtml()`, `sanitizeInput()`

### Seguridad Frontend

```javascript
// SIEMPRE usar para contenido dinámico:
escapeHtml(text)        // Escapar HTML
element.textContent     // Texto plano (seguro)
```

---

## API Patterns

### Endpoints Comunes

```bash
# Sync desde Excel
POST /api/sync
POST /api/sync-genzai
POST /api/sync-ukeoi
POST /api/sync-staff

# Leave requests workflow
POST /api/leave-requests           # crear
POST /api/leave-requests/{id}/approve  # aprobar (deduce días)
POST /api/leave-requests/{id}/reject   # rechazar
POST /api/leave-requests/{id}/revert   # revertir (restaura días)

# Compliance
GET /api/compliance/5day?year=2025
GET /api/expiring-soon?year=2025&threshold_months=3
```

---

## Common Tasks

### Agregar Nueva Columna

1. Actualizar schema en `database.py`
2. Agregar mapping en `excel_service.py`
3. Actualizar respuesta API en `main.py`
4. Actualizar frontend en `app.js`

### Debugging Excel

```bash
python test_parser.py              # Test parsing
python debug_excel.py              # Inspeccionar datos raw
sqlite3 yukyu.db ".schema"         # Ver estructura DB
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

- **Código:** Inglés (variables, funciones)
- **UI:** Japonés (labels, mensajes)
- **Documentación:** Castellano
- **Commits:** Conventional commits en inglés (`feat:`, `fix:`, `docs:`)
