# YuKyuDATA-app v2.0 - Mejoras Implementadas

## Resumen de Cambios

Este documento detalla todas las mejoras implementadas en la versión 2.0 del sistema de gestión de vacaciones.

---

## FASE 1: Seguridad

### 1.1 CORS Restringido
**Archivo:** `main.py`

**Antes:**
```python
allow_origins=["*"]  # Vulnerable
```

**Después:**
```python
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]
allow_origins=ALLOWED_ORIGINS
allow_credentials=False
allow_methods=["GET", "POST", "DELETE"]
```

### 1.2 Rate Limiter
**Archivo:** `main.py`

Nueva clase `RateLimiter`:
- Máximo 100 requests por minuto por IP
- Limpieza automática de requests antiguos
- Sin dependencias externas

### 1.3 Validación con Pydantic
**Archivo:** `main.py`

Nuevos modelos de validación:
```python
class LeaveRequestCreate(BaseModel):
    employee_num: str = Field(..., min_length=1)
    days_requested: float = Field(..., ge=0, le=40)
    leave_type: str  # Validado contra: full, half_am, half_pm, hourly
```

### 1.4 Prevención XSS
**Archivo:** `static/js/app.js`

Nuevas funciones de seguridad:
```javascript
App.utils.escapeHtml(str)   // Escapa HTML
App.utils.escapeAttr(str)   // Escapa atributos
App.utils.safeNumber(val)   // Valida números
```

Cambio de onclick inline a event delegation:
```javascript
// ANTES (vulnerable):
onclick="App.ui.openModal('${e.employeeNum}')"

// DESPUÉS (seguro):
data-employee-num="${App.utils.escapeAttr(e.employeeNum)}"
class="employee-row"
```

---

## FASE 2: Arquitectura de Base de Datos

### 2.1 Índices Estratégicos
**Archivo:** `database.py`

```sql
-- Employees
CREATE INDEX idx_emp_num ON employees(employee_num)
CREATE INDEX idx_emp_year ON employees(year)
CREATE INDEX idx_emp_num_year ON employees(employee_num, year)

-- Leave Requests
CREATE INDEX idx_lr_emp_num ON leave_requests(employee_num)
CREATE INDEX idx_lr_status ON leave_requests(status)
CREATE INDEX idx_lr_year ON leave_requests(year)
CREATE INDEX idx_lr_dates ON leave_requests(start_date, end_date)

-- Genzai/Ukeoi
CREATE INDEX idx_genzai_emp ON genzai(employee_num)
CREATE INDEX idx_genzai_status ON genzai(status)
```

### 2.2 Migraciones de Schema
**Archivo:** `database.py`

Nuevas columnas agregadas:
- `genzai.hire_date` - Fecha de entrada del empleado
- `ukeoi.hire_date` - Fecha de entrada del empleado
- `employees.grant_year` - Año de otorgamiento para tracking LIFO

### 2.3 Sistema de Logging
**Archivo:** `logger.py` (nuevo)

Características:
- Logs rotativos (10MB max, 5 backups)
- Archivo separado para errores
- Funciones especializadas:
  - `log_api_request()`
  - `log_db_operation()`
  - `log_sync_event()`
  - `log_leave_request()`
  - `log_fiscal_event()`

---

## FASE 3: Frontend

### 3.1 Corrección de XSS
**Archivo:** `static/js/app.js`

Funciones afectadas:
- `renderTable()` - Tabla de empleados
- `searchEmployee()` - Resultados de búsqueda
- `loadPending()` - Solicitudes pendientes

### 3.2 Event Delegation
**Archivo:** `static/js/app.js`

Nuevos listeners en `setupListeners()`:
- Click en filas de empleados
- Click en resultados de búsqueda
- Click en botones aprobar/rechazar
- ESC para cerrar modales

### 3.3 Mejoras de Accesibilidad
**Archivo:** `static/css/main.css`

```css
/* Screen reader only */
.sr-only { ... }

/* Focus visible para navegación por teclado */
:focus-visible { outline: 2px solid var(--primary); }

/* Skip link */
.skip-link { ... }

/* Soporte para alto contraste */
@media (prefers-contrast: high) { ... }

/* Soporte para movimiento reducido */
@media (prefers-reduced-motion: reduce) { ... }
```

### 3.4 Badge para Valores Negativos
**Archivo:** `static/css/main.css`

```css
.badge-critical {
  background: rgba(248, 113, 113, 0.2);
  color: var(--danger);
  border: 2px solid var(--danger);
  animation: pulse 1.5s ease-in-out infinite;
}
```

---

## FASE 4: Lógica de Año Fiscal

### 4.1 Nuevo Módulo
**Archivo:** `fiscal_year.py` (nuevo)

#### Tabla de Otorgamiento (Ley Laboral Japonesa)
```python
GRANT_TABLE = {
    0.5: 10,   # 6 meses
    1.5: 11,   # 1 año 6 meses
    2.5: 12,   # 2 años 6 meses
    3.5: 14,   # 3 años 6 meses
    4.5: 16,   # 4 años 6 meses
    5.5: 18,   # 5 años 6 meses
    6.5: 20,   # 6+ años (máximo)
}
```

#### Configuración Fiscal
```python
FISCAL_CONFIG = {
    'period_start_day': 21,
    'period_end_day': 20,
    'max_carry_over_years': 2,
    'max_accumulated_days': 40,
    'minimum_annual_use': 5,  # 5日取得義務
}
```

### 4.2 Funciones Principales

| Función | Descripción |
|---------|-------------|
| `calculate_seniority_years()` | Calcula antigüedad del empleado |
| `calculate_granted_days()` | Días según antigüedad |
| `get_fiscal_period()` | Período 21日〜20日 |
| `process_year_end_carryover()` | Carry-over de fin de año |
| `get_employee_balance_breakdown()` | Desglose por año (LIFO) |
| `apply_lifo_deduction()` | Deducción usando días NUEVOS primero |
| `check_expiring_soon()` | Días próximos a expirar |
| `check_5day_compliance()` | Cumplimiento de 5日取得義務 |

> **NOTA IMPORTANTE**: La lógica de consumo es **LIFO** (Last In, First Out), es decir, se consumen primero los días del año más reciente. Esto difiere de FIFO donde se consumirían los días más antiguos primero.

### 4.3 Nuevos Endpoints
**Archivo:** `main.py`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/fiscal/config` | GET | Configuración fiscal |
| `/api/fiscal/process-carryover` | POST | Procesar carry-over |
| `/api/fiscal/balance-breakdown/{emp}` | GET | Desglose LIFO |
| `/api/fiscal/expiring-soon` | GET | Días por expirar |
| `/api/fiscal/5day-compliance/{year}` | GET | Cumplimiento 5日 |
| `/api/fiscal/grant-recommendation/{emp}` | GET | Recomendación de otorgamiento |
| `/api/fiscal/apply-lifo-deduction` | POST | Aplicar deducción LIFO (nuevos primero) |

---

## FASE 5: Sincronización Excel Bidireccional

### 5.1 Nuevo Módulo
**Archivo:** `excel_export.py` (nuevo)

### 5.2 Funciones de Exportación

| Función | Descripción |
|---------|-------------|
| `create_approved_requests_excel()` | Solicitudes aprobadas |
| `create_monthly_report_excel()` | Reporte mensual (21日〜20日) |
| `create_annual_ledger_excel()` | 年次有給休暇管理簿 (legal) |
| `update_master_excel()` | Actualizar Excel maestro |
| `get_export_files()` | Listar archivos exportados |
| `cleanup_old_exports()` | Limpiar archivos antiguos |

### 5.3 Nuevos Endpoints
**Archivo:** `main.py`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/export/approved-requests` | POST | Exportar aprobadas |
| `/api/export/monthly-report` | POST | Exportar reporte mensual |
| `/api/export/annual-ledger` | POST | Exportar libro anual |
| `/api/export/download/{filename}` | GET | Descargar archivo |
| `/api/export/files` | GET | Listar archivos |
| `/api/export/cleanup` | DELETE | Limpiar antiguos |
| `/api/sync/update-master-excel` | POST | Sincronizar BD → Excel |

### 5.4 Características del Export

- **Estilos profesionales:** Headers con color, bordes, alineación
- **Múltiples hojas:** Resumen, detalle, solicitudes
- **Backups automáticos:** Antes de modificar Excel maestro
- **Directorio organizado:** `/exports/` con limpieza automática

---

## Archivos Nuevos Creados

| Archivo | Descripción |
|---------|-------------|
| `logger.py` | Sistema de logging centralizado |
| `fiscal_year.py` | Lógica de año fiscal japonés |
| `excel_export.py` | Exportación a Excel |
| `logs/` | Directorio de logs |
| `exports/` | Directorio de exportaciones |
| `docs/IMPROVEMENTS.md` | Esta documentación |

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `main.py` | CORS, Rate Limiter, Pydantic, Endpoints fiscales y export |
| `database.py` | Índices, migraciones, columnas nuevas |
| `static/js/app.js` | XSS prevention, event delegation, utils |
| `static/css/main.css` | badge-critical, accesibilidad, a11y |

---

## Uso de los Nuevos Endpoints

### Procesar Carry-Over de Fin de Año
```bash
curl -X POST "http://localhost:8000/api/fiscal/process-carryover?from_year=2024&to_year=2025"
```

### Ver Desglose de Balance (LIFO)
```bash
curl "http://localhost:8000/api/fiscal/balance-breakdown/12345?year=2025"
```

### Ver Días por Expirar
```bash
curl "http://localhost:8000/api/fiscal/expiring-soon?year=2025"
```

### Verificar Cumplimiento 5日
```bash
curl "http://localhost:8000/api/fiscal/5day-compliance/2025"
```

### Exportar Reporte Mensual
```bash
curl -X POST "http://localhost:8000/api/export/monthly-report?year=2025&month=1"
```

### Exportar Libro Anual (Legal)
```bash
curl -X POST "http://localhost:8000/api/export/annual-ledger?year=2025"
```

### Sincronizar BD → Excel
```bash
curl -X POST "http://localhost:8000/api/sync/update-master-excel?year=2025"
```

---

## Próximos Pasos Recomendados

1. **Autenticación:** Implementar JWT o OAuth2 con roles
2. **Notificaciones:** Emails al aprobar/rechazar solicitudes
3. **Dashboard Fiscal:** Vista de compliance y expiración
4. **Tests:** Añadir pruebas unitarias para nuevos módulos
5. **Backups:** Automatizar backups de BD

---

*Documentación generada: 2025-12-15*
*Versión: 2.0.0*
