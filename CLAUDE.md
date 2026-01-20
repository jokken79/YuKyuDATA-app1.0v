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
| Backend | FastAPI + SQLite/PostgreSQL + PyJWT + Alembic |
| Frontend | Vanilla JS (ES6) + Chart.js + ApexCharts |
| Testing | Pytest (1214 tests) + Jest + Playwright |

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

# Docker
docker-compose -f docker-compose.dev.yml up -d      # Desarrollo
docker-compose -f docker-compose.secure.yml up -d   # Producción

# Verificaciones
python scripts/project-status.py              # Estado CLI
```

---

## Architecture

```
Frontend (SPA)                    static/js/app.js + static/src/
       │
       │ REST API (JSON)
       ▼
API Layer (main.py + routes/)     ~50 endpoints, JWT Auth, CSRF, Rate Limiting
       │
       ▼
Service Layer (services/)         14 módulos: fiscal_year, excel, auth, reports...
       │
       ▼
Agent System (agents/)            14 agentes especializados + orchestrator
       │
       ▼
Data Layer (database.py)          SQLite/PostgreSQL, backup, audit log
```

### Key Directories

| Directorio | Propósito |
|------------|-----------|
| `routes/` | API endpoints modularizados (21 archivos) |
| `services/` | Lógica de negocio (14 módulos) |
| `agents/` | 14 agentes (compliance, security, testing, memory...) |
| `middleware/` | CSRF, rate limiting, security headers |
| `static/src/` | Frontend moderno (componentes ES6) |
| `static/js/` | Legacy SPA (app.js) |

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

### Patrones de Código
```python
# Conexión segura - SIEMPRE usar context manager
with get_db() as conn:
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE year = ?", (2025,))

# NUNCA concatenar strings en SQL
c.execute(f"SELECT * FROM employees WHERE year = {year}")  # ❌ SQL Injection
c.execute("SELECT * FROM employees WHERE year = ?", (year,))  # ✅ Parameterized
```

---

## Environment Variables

Copiar `.env.example` a `.env` y configurar:

### Críticas (REQUERIDAS en producción)
```bash
JWT_SECRET_KEY=...          # python -c "import secrets; print(secrets.token_urlsafe(32))"
DATABASE_ENCRYPTION_KEY=... # python -c "import secrets; print(secrets.token_hex(32))"
```

### Principales
```bash
DEBUG=false                 # true para desarrollo
DATABASE_TYPE=sqlite        # sqlite o postgresql
DATABASE_URL=sqlite:///./yukyu.db
CORS_ORIGINS=http://localhost:8000
RATE_LIMIT_ENABLED=true
```

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

# Leave requests workflow
POST  /api/leave-requests
PATCH /api/leave-requests/{id}/approve   # Deduce días
PATCH /api/leave-requests/{id}/reject

# Compliance
GET  /api/compliance/5day?year=2025
GET  /api/expiring-soon?year=2025&threshold_months=3

# Health
GET  /api/health
GET  /api/health/detailed
```

---

## Frontend Architecture

### Arquitectura Dual
| Sistema | Ubicación | Estado |
|---------|-----------|--------|
| **Legacy** | `static/js/app.js` | Activo (producción) |
| **Modern** | `static/src/` | Disponible para nuevas features |

### Uso Componentes Modernos
```javascript
import { Modal, Alert, DataTable } from '/static/src/components/index.js';

Alert.success('保存しました');
Alert.error('エラーが発生しました');
```

### Seguridad Frontend
```javascript
// SIEMPRE usar para contenido dinámico:
escapeHtml(text)        // Escapar HTML
element.textContent     // Texto plano (seguro)

// NUNCA usar:
innerHTML = userInput   // ❌ Vulnerabilidad XSS
```

---

## Security

- **JWT Auth:** Access 15min + Refresh 7 días
- **CSRF Protection:** Middleware activo para POST/PUT/DELETE
- **Rate Limiting:** Configurable por endpoint

### Rate Limits
| Endpoint | Límite |
|----------|--------|
| `/api/auth/login` | 5/min |
| `/api/sync*` | 2/min |
| `/api/reports/*` | 10/min |
| General (auth) | 200/min |

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

---

## Common Pitfalls

1. **ID Compuesto:** Employees usan `{emp_num}_{year}` como PK, no solo `emp_num`
2. **Período Fiscal:** 21日〜20日, no mes calendario
3. **LIFO Deduction:** Días más nuevos se deducen primero
4. **Excel Headers:** El parser detecta headers dinámicamente, no asumir posición fija
5. **Frontend Dual:** Verificar si el cambio va en `app.js` (legacy) o `static/src/` (moderno)

---

## Troubleshooting

### Puerto en uso
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Excel no se puede leer
- Verificar que el archivo existe en la raíz
- Verificar nombre exacto (caracteres japoneses)
- Cerrar Excel si está abierto

### CSRF token inválido
- Recargar la página para obtener nuevo token
- Verificar header X-CSRF-Token en requests
