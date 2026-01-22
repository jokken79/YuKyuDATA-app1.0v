# Database Adapter - Quick Start Guide

Guía rápida para empezar a usar el Database Adapter en 5 minutos.

## Instalación (Ya Incluida)

El adapter está en `/services/database_adapter.py` y listo para usar.

## Paso 1: Verificar Configuración

En `.env`:

```env
USE_ORM=false          # Usa SQL (default, seguro para producción)
LOG_LEVEL=INFO         # Cambiar a DEBUG para ver logs detallados
```

## Paso 2: Importar Funciones

```python
from services.database_adapter import (
    get_employees,
    get_employee,
    get_leave_requests,
    approve_leave_request,
    save_employees,
    get_implementation_status,
)
```

## Paso 3: Usar las Funciones

### Leer Empleados

```python
# Todos los empleados
employees = get_employees()

# Empleados de un año específico
employees = get_employees(year=2025)

# Solo empleados activos
employees = get_employees(year=2025, active_only=True)

# Con información mejorada
employees = get_employees_enhanced(year=2025)
```

### Leer Empleado Específico

```python
from services.database_adapter import get_employee

emp = get_employee(employee_num="001", year=2025)

if emp:
    print(f"Nombre: {emp['name']}")
    print(f"Balance: {emp['balance']} días")
else:
    print("Empleado no encontrado")
```

### Solicitudes de Vacaciones

```python
from services.database_adapter import (
    get_leave_requests,
    approve_leave_request,
    reject_leave_request,
)

# Solicitudes pendientes
pending = get_leave_requests(status="PENDING", year=2025)

for request in pending:
    print(f"Solicitud #{request['id']}: {request['employee_name']}")

    # Aprobar (deduce días automáticamente con LIFO)
    try:
        approve_leave_request(request_id=request['id'], approved_by="admin")
        print("✓ Aprobada")
    except ValueError as e:
        # Rechazar si no hay suficiente balance
        reject_leave_request(request_id=request['id'], approved_by="admin")
        print(f"✗ Rechazada: {e}")
```

### Guardar Empleados

```python
from services.database_adapter import save_employees

# Datos típicamente del parser de Excel
employees = [
    {
        "id": "001_2025",
        "employee_num": "001",
        "name": "田中太郎",
        "granted": 20.0,
        "used": 5.0,
        "balance": 15.0,
        "year": 2025,
    },
    # ... más empleados
]

save_employees(employees)
print(f"Guardados {len(employees)} empleados")
```

### Verificar Implementación

```python
from services.database_adapter import get_implementation_status
import json

status = get_implementation_status()
print(json.dumps(status, indent=2))

# Output:
# {
#   "use_orm": false,
#   "orm_available": true/false,
#   "implementation": "Raw SQL (database.py)",
#   "database_type": "sqlite",
#   "fallback_enabled": true,
#   "log_level": "INFO"
# }
```

## Paso 4: Cambiar Implementación (Para Dev/Testing)

Para probar con ORM en lugar de SQL:

```bash
# Terminal
export USE_ORM=true
python main.py

# O en Docker
docker run -e USE_ORM=true app
```

El código no cambia, solo la implementación subyacente.

## Paso 5: Logging y Debugging

Habilitar logs detallados:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

Verás en los logs:

```
[DEBUG] [SQL] get_employees(year=2025) called
[DEBUG] [SQL] get_employees(year=2025) completed successfully
```

## Ejemplos Completos

Ver `/examples/database_adapter_usage.py` para 12 ejemplos funcionales.

Ejecutar:

```bash
python examples/database_adapter_usage.py
```

## API Reference

### Employee Functions

```python
get_employees(year=None, active_only=False) → List[Dict]
get_employee(employee_num, year) → Optional[Dict]
get_employees_enhanced(year=None, active_only=False) → List[Dict]
get_available_years() → List[int]
save_employee(employee_data) → None
save_employees(employees_data) → None
get_employee_total_balance(employee_num, year) → float
get_employee_yukyu_history(employee_num, current_year=None) → List[Dict]
```

### Leave Request Functions

```python
get_leave_requests(status=None, employee_num=None, year=None) → List[Dict]
get_leave_request(request_id) → Optional[Dict]
approve_leave_request(request_id, approved_by) → bool
reject_leave_request(request_id, approved_by) → bool
```

### Employee Type Functions

```python
get_genzai(status=None, year=None, active_in_year=False) → List[Dict]
get_ukeoi(status=None, year=None, active_in_year=False) → List[Dict]
get_staff(status=None, year=None, active_in_year=False) → List[Dict]
save_genzai(genzai_data) → None
save_ukeoi(ukeoi_data) → None
save_staff(staff_data) → None
```

### Usage Detail Functions

```python
get_yukyu_usage_details(employee_num=None, year=None, month=None) → List[Dict]
save_yukyu_usage_details(usage_details_list) → None
get_monthly_usage_summary(year) → Dict[int, Dict]
get_employee_usage_summary(employee_num, year) → Optional[Dict]
```

### Audit & Notification Functions

```python
get_audit_log(entity_type=None, entity_id=None, limit=100) → List[Dict]
get_notifications(user_id) → List[Dict]
get_read_notification_ids(user_id) → set
```

## Pattern: Use en FastAPI

```python
from fastapi import FastAPI, HTTPException
from services.database_adapter import get_employees, get_leave_requests

app = FastAPI()

@app.get("/api/employees")
async def list_employees(year: int = 2025):
    """Get all employees for a year."""
    try:
        employees = get_employees(year=year)
        return {"data": employees, "count": len(employees)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leave-requests")
async def list_leave_requests(status: str = "PENDING"):
    """Get leave requests by status."""
    requests = get_leave_requests(status=status)
    return {"data": requests, "count": len(requests)}
```

## Pattern: Use en Services

```python
from services.database_adapter import (
    get_leave_requests,
    approve_leave_request,
    get_employee,
)

def approve_pending_requests():
    """Batch approve all pending requests (if balance available)."""
    pending = get_leave_requests(status="PENDING", year=2025)

    for request in pending:
        emp = get_employee(request['employee_num'], request['year'])

        if emp and emp['balance'] >= request['days_requested']:
            try:
                approve_leave_request(
                    request_id=request['id'],
                    approved_by="system"
                )
                print(f"✓ Approved: {request['employee_name']}")
            except Exception as e:
                print(f"✗ Error: {e}")
```

## Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'database_orm'"

Solución: Asegúrate que `database_orm.py` existe o cambia `USE_ORM=false` (SQL fallback).

### Problema: Resultados diferentes entre SQL y ORM

Solución:

```bash
# 1. Habilitar DEBUG logging
export LOG_LEVEL=DEBUG

# 2. Comparar resultados
export USE_ORM=false
python -c "from services.database_adapter import get_employees; \
           print(len(get_employees(year=2025)))"

export USE_ORM=true
python -c "from services.database_adapter import get_employees; \
           print(len(get_employees(year=2025)))"

# 3. Reportar diferencias
```

### Problema: Slow queries

Solución:

```bash
# Usa SQL (más optimizado que ORM)
export USE_ORM=false

# O usa indexes en BD
# Ver docs/DATABASE_ADAPTER.md > Performance Considerations
```

## Testing

Ejecutar tests:

```bash
# Todos con SQL
pytest tests/test_database_adapter.py -v

# Todos con ORM
USE_ORM=true pytest tests/test_database_adapter.py -v

# Solo rápidos (skip integration)
pytest tests/test_database_adapter.py -v -m "not integration"
```

## Checklist: First Time Setup

- [ ] Leer este documento (5 min)
- [ ] Ver `docs/DATABASE_ADAPTER.md` (10 min)
- [ ] Ejecutar `examples/database_adapter_usage.py` (5 min)
- [ ] Ejecutar tests: `pytest tests/test_database_adapter.py -v` (2 min)
- [ ] Usar en un endpoint: `get_employees(year=2025)` (5 min)
- [ ] Cambiar a ORM y verificar: `USE_ORM=true` (5 min)

Total: ~30 minutos para entender completamente.

## Recursos

- `services/database_adapter.py` - Código principal (30 KB)
- `docs/DATABASE_ADAPTER.md` - Documentación completa
- `examples/database_adapter_usage.py` - 12 ejemplos
- `tests/test_database_adapter.py` - 40+ tests
- `IMPLEMENTATION_SUMMARY.md` - Resumen técnico

## ¿Preguntas?

1. ¿Cómo cambio a ORM? → `export USE_ORM=true`
2. ¿Qué pasa si ORM falla? → Fallback automático a SQL
3. ¿Puedo usar ambas al mismo tiempo? → Sí, con logging
4. ¿Cuándo debería migrar a ORM? → Cuando Phase 2 esté completa

---

**Próximos pasos:**

1. Leer `/docs/DATABASE_ADAPTER.md` para detalles
2. Revisar `/examples/database_adapter_usage.py` para patrones
3. Ejecutar `/tests/test_database_adapter.py` para validar
4. Integrar en tus endpoints FastAPI
