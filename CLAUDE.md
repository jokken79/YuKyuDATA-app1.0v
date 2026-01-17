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
```

---

## Project Overview

**YuKyuDATA-app** es un sistema de gestión de empleados especializado en cumplimiento de la ley laboral japonesa para vacaciones pagadas (有給休暇).

**Versión actual:** v5.3 (ver `CLAUDE_MEMORY.md` para historial completo)

**Tech Stack:**
- **Backend:** FastAPI + SQLite + PyJWT (auth)
- **Frontend:** Vanilla JavaScript (ES6 modules) + Chart.js + ApexCharts
- **Estilos:** Glassmorphism design system
- **DevOps:** Docker + GitHub Actions CI/CD

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
pytest tests/ -v                                    # Todos los tests
pytest tests/test_api.py::test_sync_employees       # Test individual
pytest tests/test_fiscal_year.py -v                 # Tests críticos fiscal
pytest tests/test_lifo_deduction.py -v              # Tests LIFO
npx jest                                            # Tests frontend
npx playwright test                                 # E2E tests

# Docker
./scripts/docker-dev.sh                             # Iniciar desarrollo
./scripts/docker-dev.sh --stop                      # Detener
docker-compose -f docker-compose.dev.yml up -d      # Alternativa

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
│  static/js/app.js + modules/ (ES6)                         │
│  Chart.js + ApexCharts | Glassmorphism CSS                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────▼───────────────────────────────────────┐
│                 API Layer (main.py)                         │
│  FastAPI endpoints (~30) | JWT Auth | CSRF Protection      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Service Layer                                 │
│  excel_service.py (parsing) | fiscal_year.py (ley laboral) │
│  notifications.py | reports.py (PDF)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Data Layer (database.py)                     │
│  SQLite CRUD | Backup system | Audit log                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Database (yukyu.db)                         │
│  7+ tablas | 15+ índices | FK constraints                  │
└─────────────────────────────────────────────────────────────┘
```

### Archivos Clave

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `main.py` | 5,500+ | FastAPI app con ~30 endpoints |
| `database.py` | 1,400+ | SQLite CRUD, backups, audit log |
| `excel_service.py` | 800+ | Parsing inteligente de Excel (medio día, comentarios) |
| `fiscal_year.py` | 500+ | **CRÍTICO** - Lógica de ley laboral japonesa |
| `static/js/app.js` | 4,800+ | SPA principal con módulos App.* |
| `static/js/modules/` | - | 8+ módulos ES6 (data-service, i18n, etc.) |
| `agents/` | - | Agentes: memory, compliance, orchestrator |

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

| Módulo | Propósito |
|--------|-----------|
| `data-service.js` | Cliente API con cache 5 min |
| `chart-manager.js` | Chart.js + ApexCharts |
| `ui-manager.js` | DOM manipulation |
| `virtual-table.js` | Virtual scrolling para 1000+ filas |
| `utils.js` | XSS prevention: `escapeHtml()`, `sanitizeInput()` |
| `i18n.js` | Internacionalización (ja/es/en) |
| `offline-storage.js` | IndexedDB para modo offline |
| `ui-enhancements.js` | Form validation, tooltips, modales |
| `leave-requests-manager.js` | Gestión de solicitudes |

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

# Leave requests workflow
POST /api/leave-requests                    # Crear solicitud
POST /api/leave-requests/{id}/approve       # Aprobar (deduce días)
POST /api/leave-requests/{id}/reject        # Rechazar
POST /api/leave-requests/{id}/revert        # Revertir (restaura días)

# Compliance
GET  /api/compliance/5day?year=2025
GET  /api/expiring-soon?year=2025&threshold_months=3

# Notificaciones
GET  /api/notifications                     # Lista con is_read
POST /api/notifications/{id}/mark-read      # Marcar como leída
POST /api/notifications/mark-all-read       # Marcar todas
GET  /api/notifications/unread-count        # Conteo no leídas

# Yukyu Details (edición individual)
GET  /api/yukyu/usage-details/{emp}/{year}  # Obtener detalles
POST /api/yukyu/usage-details               # Crear
PUT  /api/yukyu/usage-details/{id}          # Actualizar
DELETE /api/yukyu/usage-details/{id}        # Eliminar
POST /api/yukyu/recalculate/{emp}/{year}    # Recalcular totales

# Status & Monitoring
GET  /status                                # Dashboard HTML
GET  /api/project-status                    # Estado JSON
GET  /api/health                            # Health check
```

---

## Security Considerations

### Backend
- **CSRF Protection:** Middleware activo para POST/PUT/DELETE
- **JWT Auth:** Tokens con expiración, refresh automático
- **SQL Injection:** Siempre usar parámetros `?` en queries
- **Rate Limiting:** Implementado en endpoints críticos

### Frontend
- **XSS Prevention:** Usar `escapeHtml()` para todo input de usuario
- **CSP:** Headers configurados (strict-dynamic, no unsafe-inline)
- **Fetch Timeout:** AbortController con 30s timeout

### Datos Sensibles
- No commitear archivos Excel con datos reales
- `.env` para configuración sensible (no commitear)
- Backups encriptados en producción

---

## Common Tasks

### Agregar Nueva Columna

1. Actualizar schema en `database.py`
2. Agregar mapping en `excel_service.py`
3. Actualizar respuesta API en `main.py`
4. Actualizar frontend en `app.js`
5. Agregar tests en `tests/`

### Agregar Nuevo Endpoint

1. Definir ruta en `main.py`
2. Implementar lógica en service layer si es compleja
3. Agregar validación con Pydantic models
4. Documentar con docstrings (aparece en /docs)
5. Agregar tests

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
```

### Código JavaScript
```javascript
// Usar ES6 modules
import { escapeHtml } from './modules/utils.js';

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

---

## Claude Session Checklist

### Al iniciar sesión:
1. ✅ Leer `CLAUDE_MEMORY.md` para contexto histórico
2. ✅ Verificar estado git: `git status`, `git log -3`
3. ✅ Revisar TODOs pendientes
4. ✅ Ejecutar `python scripts/project-status.py`

### Antes de implementar:
1. ✅ Verificar si ya existe funcionalidad similar
2. ✅ Revisar patrones establecidos en código existente
3. ✅ Usar `App.editYukyu` como referencia para modales

### Al terminar sesión:
1. ✅ Actualizar `CLAUDE_MEMORY.md` con nuevos aprendizajes
2. ✅ Documentar errores encontrados y soluciones
3. ✅ Agregar features implementadas al historial
