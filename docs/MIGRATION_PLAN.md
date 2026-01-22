# Plan de Migracion YuKyuDATA

**Version:** 1.0
**Fecha:** 2026-01-22
**Estado:** Borrador para revision
**Arquitecto:** Claude (ARCHITECT Mode)

---

## Resumen Ejecutivo

Este plan cubre tres migraciones criticas que deben ejecutarse de forma incremental:

| Area | Estado Actual | Estado Final | Riesgo | Duracion Est. |
|------|---------------|--------------|--------|---------------|
| ORM Migration | 47% (~40/85 funciones) | 100% SQLAlchemy | MEDIO | 4-6 semanas |
| Frontend Unification | Dual (7,530 LOC legacy) | Moderno unico | ALTO | 8-12 semanas |
| Routes Deprecation | v0 + v1 activos | Solo v1 | BAJO | 2-3 semanas |

**Orden de ejecucion recomendado:**
1. Routes Deprecation (menor riesgo, libera cognitive load)
2. ORM Migration (prerequisito para nuevas features)
3. Frontend Unification (mayor esfuerzo, puede paralelizarse parcialmente)

---

## Parte 1: Deprecacion de Routes v0

### 1.1 Estado Actual

```
routes/           (v0) - 21 archivos, prefix="/api"
routes/v1/        (v1) - 19 archivos, prefix="/api/v1"
main.py           - AMBOS registrados (lineas 326-346)
```

**Diferencias detectadas entre v0 y v1:**
- Import paths: `.dependencies` vs `..dependencies`
- Prefix: `"/api"` vs `""` (v1 usa router_v1 con prefix `/api/v1`)
- Respuestas: v0 tiene `available_years` adicional en algunos endpoints
- v0 usa `parse_yukyu_usage_details_enhanced`, v1 usa version base

### 1.2 Estrategia: Redirect Gradual

```
FASE 1: Agregar deprecation warnings
FASE 2: Redirect automatico v0 -> v1
FASE 3: Periodo de observacion
FASE 4: Eliminar v0
```

### 1.3 Fases Detalladas

#### FASE 1.1: Agregar Deprecation Middleware (Semana 1)

**Archivo a crear:** `middleware/deprecation.py`

```python
# middleware/deprecation.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

DEPRECATED_ROUTES = {
    "/api/employees": "/api/v1/employees",
    "/api/leave-requests": "/api/v1/leave-requests",
    # ... mapeo completo
}

class DeprecationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in DEPRECATED_ROUTES and not path.startswith("/api/v1"):
            # Log deprecation warning
            logger.warning(f"DEPRECATED: {path} -> use {DEPRECATED_ROUTES[path]}")

            # Add deprecation header
            response = await call_next(request)
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = "2026-03-01"
            response.headers["Link"] = f'<{DEPRECATED_ROUTES[path]}>; rel="successor-version"'
            return response

        return await call_next(request)
```

**Entregables:**
- [ ] `middleware/deprecation.py` creado
- [ ] Middleware registrado en main.py
- [ ] Tests de deprecation headers

**Comando de verificacion:**
```bash
curl -I http://localhost:8000/api/employees
# Debe incluir: Deprecation: true
```

#### FASE 1.2: Actualizar Frontend para v1 (Semana 1-2)

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `static/js/app.js` | `apiBase: '/api'` -> `apiBase: '/api/v1'` |
| `static/src/config/constants.js` | Actualizar API_BASE |
| `static/src/managers/*.js` | Verificar endpoints |

**Script de busqueda:**
```bash
# Encontrar todas las referencias a /api/ (sin v1)
grep -rn "'/api/" static/js/ static/src/ --include="*.js" | grep -v "/api/v1"
```

**Entregables:**
- [ ] app.js actualizado
- [ ] constants.js actualizado
- [ ] Managers verificados
- [ ] Tests E2E pasando

**Verificacion:**
```bash
# Verificar que no hay llamadas a v0
grep -rn "fetch.*'/api/" static/ --include="*.js" | grep -v v1 | wc -l
# Debe ser 0
```

#### FASE 1.3: Periodo de Observacion (Semana 2-3)

**Monitoreo requerido:**
```bash
# Agregar a logs
grep "DEPRECATED" logs/app.log | wc -l  # Debe tender a 0
```

**Dashboard de metricas:**
- Requests a /api/* (sin v1)
- Requests a /api/v1/*
- Ratio v0/v1

**Criterio de exito:** < 1% requests a v0 durante 7 dias consecutivos

#### FASE 1.4: Eliminar v0 (Semana 3)

**Archivos a eliminar:**
```bash
rm routes/employees.py
rm routes/leave_requests.py
rm routes/notifications.py
rm routes/yukyu.py
rm routes/compliance.py
rm routes/compliance_advanced.py
rm routes/fiscal.py
rm routes/analytics.py
rm routes/reports.py
rm routes/export.py
rm routes/auth.py
rm routes/system.py
rm routes/health.py
rm routes/calendar.py
rm routes/genzai.py
rm routes/ukeoi.py
rm routes/staff.py
rm routes/github.py
# MANTENER: routes/__init__.py, routes/dependencies.py, routes/responses.py
```

**Modificar main.py:**
```python
# ELIMINAR lineas 326-343 (include_router de v0)
# MANTENER linea 346: app.include_router(router_v1)
```

**Modificar routes/__init__.py:**
```python
# Solo exportar response helpers y dependencies
from .responses import (
    APIResponse, success_response, error_response, ...
)
# ELIMINAR exports de routers
```

**Verificacion final:**
```bash
pytest tests/ -v --tb=short
# Todos los tests deben pasar

curl http://localhost:8000/api/employees
# Debe retornar 404

curl http://localhost:8000/api/v1/employees
# Debe retornar 200
```

### 1.4 Matriz de Riesgos - Routes

| Riesgo | Prob. | Impacto | Mitigacion |
|--------|-------|---------|------------|
| Clientes externos usando v0 | Media | Alto | Comunicar sunset, 30 dias aviso |
| Tests hardcodeados a v0 | Alta | Medio | Actualizar tests primero |
| Service workers cacheando v0 | Media | Medio | Invalidar cache SW |
| Mobile apps usando v0 | Baja | Alto | N/A (no hay apps moviles) |

### 1.5 Checklist Final - Routes

- [ ] Deprecation middleware activo
- [ ] Frontend 100% en v1
- [ ] Metricas muestran 0 requests v0
- [ ] Archivos v0 eliminados
- [ ] routes/__init__.py simplificado
- [ ] main.py limpio
- [ ] Tests actualizados y pasando
- [ ] Documentacion actualizada

---

## Parte 2: Migracion ORM Completa

### 2.1 Estado Actual

```
database.py        - 3,224 lineas, ~85 funciones (raw SQL)
database_orm.py    - 1,079 lineas, ~40 funciones (SQLAlchemy)
orm/models/        - 12 modelos SQLAlchemy
repositories/      - 11 repositorios
```

**Funciones migradas (40/85 = 47%):**
- [x] get_employees_orm
- [x] get_employee_orm
- [x] get_available_years_orm
- [x] get_employees_enhanced_orm
- [x] get_leave_requests_orm
- [x] get_leave_request_orm
- [x] get_yukyu_usage_details_orm
- [x] get_notifications_orm
- [x] get_genzai_orm / get_ukeoi_orm / get_staff_orm
- [x] create_leave_request_orm
- [x] approve_leave_request_orm
- [x] update_employee_orm
- [x] ... (ver database_orm.py para lista completa)

**Funciones pendientes (~45):**
- [ ] save_employees (bulk insert)
- [ ] save_genzai / save_ukeoi / save_staff
- [ ] validate_balance_limit
- [ ] get_employee_total_balance
- [ ] get_employee_hourly_wage
- [ ] bulk_update_employees
- [ ] revert_bulk_update
- [ ] get_bulk_update_history
- [ ] create_backup / restore_backup
- [ ] log_audit
- [ ] get_audit_log / get_audit_stats
- [ ] cleanup_old_audit_logs
- [ ] Todas las funciones de refresh_tokens
- [ ] get_stats_by_factory
- [ ] get_monthly_usage_summary
- [ ] recalculate_employee_from_details
- [ ] delete_old_yukyu_records

### 2.2 Estrategia: Feature Flag + Adapter Pattern

```python
# config/feature_flags.py
USE_ORM = os.getenv('USE_ORM', 'false').lower() == 'true'

# services/employee_service.py
from config.feature_flags import USE_ORM

if USE_ORM:
    from database_orm import get_employees_orm as get_employees
else:
    from database import get_employees
```

### 2.3 Fases Detalladas

#### FASE 2.1: Completar Funciones Criticas (Semana 1-2)

**Prioridad 1 - Sync Operations (usadas en /api/sync):**

```python
# database_orm.py - AGREGAR

def save_employees_orm(employees_data: List[Dict]) -> int:
    """
    Bulk upsert de empleados.
    Equivalente a save_employees() en database.py linea 490.
    """
    with get_orm_session() as session:
        saved = 0
        for emp_data in employees_data:
            emp_id = f"{emp_data['employee_num']}_{emp_data['year']}"
            existing = session.query(Employee).filter_by(id=emp_id).first()

            if existing:
                for key, value in emp_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                new_emp = Employee(id=emp_id, **emp_data)
                session.add(new_emp)
            saved += 1

        return saved

def save_genzai_orm(genzai_data: List[Dict]) -> int:
    """Bulk upsert de empleados genzai."""
    # Similar pattern...

def save_ukeoi_orm(ukeoi_data: List[Dict]) -> int:
    """Bulk upsert de empleados ukeoi."""
    # Similar pattern...

def save_staff_orm(staff_data: List[Dict]) -> int:
    """Bulk upsert de empleados staff."""
    # Similar pattern...
```

**Entregables:**
- [ ] save_employees_orm implementado y testeado
- [ ] save_genzai_orm implementado y testeado
- [ ] save_ukeoi_orm implementado y testeado
- [ ] save_staff_orm implementado y testeado

**Test de verificacion:**
```bash
pytest tests/orm/test_phase2_write_operations.py -v
```

#### FASE 2.2: Funciones de Negocio (Semana 2-3)

**Prioridad 2 - Business Logic:**

```python
# database_orm.py - AGREGAR

def validate_balance_limit_orm(employee_num: str, year: int, additional_days: float = 0) -> bool:
    """
    Valida que el balance no exceda 40 dias.
    Equivalente a database.py linea 431.
    """
    with get_orm_session() as session:
        emp = session.query(Employee).filter_by(
            employee_num=employee_num, year=year
        ).first()

        if not emp:
            return True

        total = (emp.balance or 0) + additional_days
        return total <= 40.0

def get_employee_hourly_wage_orm(employee_num: str) -> float:
    """
    Obtiene salario por hora desde genzai, ukeoi o staff.
    Equivalente a database.py linea 1227.
    """
    with get_orm_session() as session:
        # Check genzai first
        genzai = session.query(GenzaiEmployee).filter_by(
            employee_num=employee_num
        ).first()
        if genzai and genzai.hourly_wage:
            return float(genzai.hourly_wage)

        # Then ukeoi
        ukeoi = session.query(UkeoiEmployee).filter_by(
            employee_num=employee_num
        ).first()
        if ukeoi and ukeoi.hourly_wage:
            return float(ukeoi.hourly_wage)

        # Then staff
        staff = session.query(StaffEmployee).filter_by(
            employee_num=employee_num
        ).first()
        if staff and staff.hourly_wage:
            return float(staff.hourly_wage)

        return 0.0

def recalculate_employee_used_days_orm(employee_num: str, year: int) -> Dict:
    """
    Recalcula dias usados desde yukyu_usage_detail.
    Equivalente a database.py linea 1757.
    """
    with get_orm_session() as session:
        # Sum usage details
        total_used = session.query(func.sum(YukyuUsageDetail.days_used)).filter(
            YukyuUsageDetail.employee_num == employee_num,
            YukyuUsageDetail.year == year
        ).scalar() or 0.0

        # Update employee
        emp = session.query(Employee).filter_by(
            employee_num=employee_num, year=year
        ).first()

        if emp:
            emp.used = total_used
            emp.balance = (emp.granted or 0) - total_used
            return emp.to_dict()

        return None
```

**Entregables:**
- [ ] validate_balance_limit_orm
- [ ] get_employee_hourly_wage_orm
- [ ] recalculate_employee_used_days_orm
- [ ] get_stats_by_factory_orm
- [ ] get_monthly_usage_summary_orm

#### FASE 2.3: Bulk Operations (Semana 3-4)

**Prioridad 3 - Bulk Updates (admin operations):**

```python
# database_orm.py - AGREGAR

def bulk_update_employees_orm(
    employee_nums: List[str],
    year: int,
    updates: Dict[str, Any],
    updated_by: str = "system"
) -> Dict[str, Any]:
    """
    Actualiza multiples empleados atomicamente.
    Equivalente a database.py linea 2427.
    """
    import uuid
    operation_id = str(uuid.uuid4())[:8]

    with get_orm_session() as session:
        updated = []
        errors = []

        for emp_num in employee_nums:
            try:
                emp = session.query(Employee).filter_by(
                    employee_num=emp_num, year=year
                ).first()

                if emp:
                    # Store old values for revert
                    old_values = emp.to_dict()

                    # Apply updates
                    for key, value in updates.items():
                        if hasattr(emp, key):
                            setattr(emp, key, value)

                    updated.append({
                        'employee_num': emp_num,
                        'old_values': old_values,
                        'new_values': emp.to_dict()
                    })
                else:
                    errors.append({'employee_num': emp_num, 'error': 'Not found'})
            except Exception as e:
                errors.append({'employee_num': emp_num, 'error': str(e)})

        # Log to bulk_audit table
        # ... (similar to database.py)

        return {
            'operation_id': operation_id,
            'updated': len(updated),
            'errors': len(errors),
            'details': updated,
            'error_details': errors
        }
```

**Entregables:**
- [ ] bulk_update_employees_orm
- [ ] revert_bulk_update_orm
- [ ] get_bulk_update_history_orm
- [ ] Tests de atomicidad

#### FASE 2.4: Audit y Tokens (Semana 4-5)

**Prioridad 4 - Security & Audit:**

```python
# database_orm.py - AGREGAR

def log_audit_orm(
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: str = None,
    old_value: Any = None,
    new_value: Any = None,
    ip_address: str = None,
    user_agent: str = None,
    metadata: Dict = None
) -> str:
    """
    Registra evento de auditoria.
    Equivalente a database.py linea 2138.
    """
    import uuid
    audit_id = str(uuid.uuid4())

    with get_orm_session() as session:
        audit = AuditLog(
            id=audit_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow()
        )
        session.add(audit)
        return audit_id

# Refresh token functions
def store_refresh_token_orm(...) -> bool:
    ...

def get_refresh_token_by_hash_orm(token_hash: str) -> Optional[Dict]:
    ...

def revoke_refresh_token_orm(token_hash: str) -> bool:
    ...
```

**Entregables:**
- [ ] log_audit_orm
- [ ] get_audit_log_orm
- [ ] get_audit_stats_orm
- [ ] cleanup_old_audit_logs_orm
- [ ] Todas las funciones de refresh_token_orm
- [ ] Tests de seguridad

#### FASE 2.5: Backup y Utilidades (Semana 5-6)

**Prioridad 5 - Utilities:**

```python
# database_orm.py - AGREGAR

def create_backup_orm(backup_dir: str = "backups") -> Dict:
    """
    Crea backup de la base de datos.
    Para SQLite: copia el archivo.
    Para PostgreSQL: pg_dump via subprocess.
    """
    from pathlib import Path
    import shutil

    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if USE_POSTGRESQL:
        # PostgreSQL backup
        filename = f"yukyu_backup_{timestamp}.sql"
        # subprocess.run(['pg_dump', ...])
        ...
    else:
        # SQLite backup
        filename = f"yukyu_backup_{timestamp}.db"
        shutil.copy2(DB_NAME, backup_path / filename)

    return {
        'filename': filename,
        'path': str(backup_path / filename),
        'timestamp': timestamp,
        'size': os.path.getsize(backup_path / filename)
    }
```

**Entregables:**
- [ ] create_backup_orm
- [ ] list_backups_orm
- [ ] restore_backup_orm
- [ ] delete_old_yukyu_records_orm
- [ ] clear_* functions

### 2.4 Integracion y Switchover

#### FASE 2.6: Feature Flag Integration (Semana 6)

**Archivo:** `config/database_config.py`

```python
import os
from functools import wraps

USE_ORM = os.getenv('USE_ORM', 'false').lower() == 'true'

def orm_or_legacy(orm_func, legacy_func):
    """
    Decorator/helper para elegir funcion ORM o legacy.
    """
    @wraps(orm_func)
    def wrapper(*args, **kwargs):
        if USE_ORM:
            return orm_func(*args, **kwargs)
        return legacy_func(*args, **kwargs)
    return wrapper
```

**Archivo:** `services/database_adapter.py`

```python
from config.database_config import USE_ORM

if USE_ORM:
    from database_orm import (
        get_employees_orm as get_employees,
        get_employee_orm as get_employee,
        save_employees_orm as save_employees,
        # ... todas las funciones
    )
else:
    from database import (
        get_employees,
        get_employee,
        save_employees,
        # ... todas las funciones
    )

# Re-export para compatibilidad
__all__ = [
    'get_employees',
    'get_employee',
    'save_employees',
    # ...
]
```

**Modificar archivos que importan database:**
```bash
# 27 archivos a modificar
sed -i 's/from database import/from services.database_adapter import/g' \
    services/*.py routes/*.py main.py
```

#### FASE 2.7: Testing Paralelo (Semana 6)

**Script:** `scripts/test_orm_parity.py`

```python
#!/usr/bin/env python3
"""
Verifica que ORM y legacy devuelven resultados identicos.
"""
import os
os.environ['USE_ORM'] = 'false'
from database import get_employees as get_employees_legacy

os.environ['USE_ORM'] = 'true'
from database_orm import get_employees_orm

def test_parity():
    legacy = get_employees_legacy(year=2025)
    orm = get_employees_orm(year=2025)

    assert len(legacy) == len(orm), f"Count mismatch: {len(legacy)} vs {len(orm)}"

    for l, o in zip(legacy, orm):
        for key in l.keys():
            assert l[key] == o.get(key), f"Mismatch for {key}: {l[key]} vs {o.get(key)}"

    print("PARITY TEST PASSED")

if __name__ == '__main__':
    test_parity()
```

**Comando:**
```bash
python scripts/test_orm_parity.py
pytest tests/orm/ -v --tb=short
```

### 2.5 Matriz de Riesgos - ORM

| Riesgo | Prob. | Impacto | Mitigacion |
|--------|-------|---------|------------|
| Diferencias en NULL handling | Alta | Medio | Tests de paridad exhaustivos |
| Performance degradation | Media | Alto | Benchmarks antes/despues |
| Transaction isolation diferente | Media | Alto | Tests de concurrencia |
| PostgreSQL vs SQLite differences | Alta | Medio | Tests en ambos DBs |
| Rollback necesario | Baja | Alto | Feature flag permite rollback instantaneo |

### 2.6 Checklist Final - ORM

- [ ] 100% funciones tienen version _orm
- [ ] Tests de paridad pasan para todas las funciones
- [ ] Benchmarks muestran performance aceptable
- [ ] Feature flag funciona correctamente
- [ ] Rollback testeado
- [ ] database.py marcado como deprecated
- [ ] Documentacion actualizada
- [ ] USE_ORM=true en produccion por 2 semanas sin issues
- [ ] database.py eliminado

---

## Parte 3: Unificacion Frontend

### 3.1 Estado Actual

```
static/js/app.js          - 7,530 lineas (LEGACY - en produccion)
static/src/               - 41 archivos (MODERNO - parcialmente usado)
  components/             - 17 componentes
  pages/                  - 8 paginas
  managers/               - 7 managers
  store/                  - 2 archivos state
  legacy-bridge/          - 1 bridge existente
```

**Dependencias del Legacy (app.js):**
- Chart.js / ApexCharts (graficos)
- i18n (traducciones)
- Auth (JWT handling)
- Theme manager (dark/light)
- UI components (alerts, modals, tables)
- All business logic

**Funcionalidades en Moderno (static/src/):**
- Componentes UI (Modal, Alert, Table, etc.)
- Pages structure
- Managers structure
- State management
- Legacy bridge

### 3.2 Estrategia: Strangler Fig Pattern

```
FASE 1: Fortalecer bridge existente
FASE 2: Migrar paginas una por una
FASE 3: Migrar utilidades compartidas
FASE 4: Eliminar legacy
```

### 3.3 Fases Detalladas

#### FASE 3.1: Completar Bridge y State (Semana 1-2)

**Objetivo:** Asegurar que el state es compartido perfectamente entre legacy y moderno.

**Archivo:** `static/src/legacy-bridge/unified-state-bridge.js`

```javascript
// Agregar sincronizacion bidireccional completa
export function initUnifiedStateBridge(legacyApp) {
    if (!legacyApp) {
        console.warn('Legacy App not provided');
        return null;
    }

    const unifiedState = getUnifiedState();

    // Sync legacy -> unified
    const originalSetState = legacyApp.state;
    Object.defineProperty(legacyApp, 'state', {
        get() { return originalSetState; },
        set(newState) {
            Object.assign(originalSetState, newState);
            unifiedState.sync(newState);
        }
    });

    // Sync unified -> legacy
    unifiedState.subscribe((key, value) => {
        if (legacyApp.state[key] !== value) {
            legacyApp.state[key] = value;
            // Trigger legacy update if needed
            if (legacyApp.updateView) {
                legacyApp.updateView();
            }
        }
    });

    return unifiedState;
}
```

**Entregables:**
- [ ] Bridge bidireccional completo
- [ ] Tests de sincronizacion
- [ ] Documentacion de API del bridge

#### FASE 3.2: Migrar Pagina Dashboard (Semana 2-4)

**Estrategia:** El Dashboard es la pagina mas visible. Migrarlo primero establece el patron.

**Extraer de app.js:**
```javascript
// LINEAS A MOVER: ~500-800 (dashboard functions)
// loadDashboardData()
// renderDashboard()
// updateCharts()
// calculateSummaryStats()
```

**Destino:** `static/src/pages/Dashboard.js`

```javascript
// static/src/pages/Dashboard.js
import { DashboardManager } from '../managers/DashboardManager.js';
import { Card, Loader, UIStates } from '../components/index.js';
import { getUnifiedState } from '../store/unified-state.js';

export const Dashboard = {
    name: 'dashboard',
    manager: null,

    async init() {
        this.manager = new DashboardManager();
        await this.manager.init();
    },

    async render() {
        const state = getUnifiedState();
        const container = document.getElementById('dashboard-view');

        if (!container) return;

        UIStates.showLoading(container);

        try {
            const data = await this.manager.loadData(state.get('year'));
            this.renderContent(container, data);
        } catch (error) {
            UIStates.showError(container, error.message);
        }
    },

    renderContent(container, data) {
        // Render dashboard cards, charts, etc.
        container.innerHTML = `
            <div class="dashboard-grid">
                ${this.renderSummaryCards(data.summary)}
                ${this.renderCharts(data.charts)}
                ${this.renderRecentActivity(data.recent)}
            </div>
        `;
    },

    // ... helper methods

    cleanup() {
        if (this.manager) {
            this.manager.cleanup();
        }
    }
};
```

**Modificar app.js:**
```javascript
// En app.js, reemplazar dashboard con delegacion
switchView(view) {
    // ... existing code ...

    if (view === 'dashboard') {
        // Delegar al modulo moderno
        if (window.YuKyuApp && window.YuKyuApp.pages.Dashboard) {
            window.YuKyuApp.pages.Dashboard.render();
            return;
        }
    }

    // ... fallback to legacy
}
```

**Test de verificacion:**
```javascript
// tests/js/dashboard.test.js
describe('Dashboard Migration', () => {
    it('should render same content as legacy', async () => {
        const legacyHTML = await renderLegacyDashboard();
        const modernHTML = await renderModernDashboard();

        // Compare key elements
        expect(modernHTML).toContain('dashboard-summary');
        expect(modernHTML).toContain('chart-container');
    });
});
```

**Entregables:**
- [ ] Dashboard.js completo con toda la funcionalidad
- [ ] DashboardManager con logica de negocio
- [ ] app.js delega a moderno
- [ ] Tests pasando
- [ ] Visual regression tests

#### FASE 3.3: Migrar Pagina Employees (Semana 4-6)

**Complejidad:** ALTA (tabla con filtros, busqueda, edicion inline, bulk operations)

**Extraer de app.js:**
```javascript
// LINEAS A MOVER: ~800-1500
// loadEmployees()
// renderEmployeesTable()
// filterEmployees()
// searchEmployees()
// editEmployee()
// bulkUpdateEmployees()
```

**Componentes necesarios:**
- [ ] Table.js mejorado con sorting, filtering
- [ ] Pagination.js
- [ ] SearchInput.js
- [ ] BulkActionBar.js
- [ ] EmployeeEditModal.js

**Entregables:**
- [ ] Employees.js completo
- [ ] EmployeesManager con toda la logica
- [ ] Componentes especializados
- [ ] Tests de funcionalidad completa

#### FASE 3.4: Migrar Paginas Restantes (Semana 6-10)

| Pagina | Complejidad | Semana |
|--------|-------------|--------|
| LeaveRequests | Alta | 6-7 |
| Analytics | Media | 7-8 |
| Compliance | Media | 8-9 |
| Settings | Baja | 9 |
| Notifications | Baja | 9-10 |

**Para cada pagina:**
1. Identificar funciones en app.js
2. Mover a static/src/pages/[Page].js
3. Crear/extender Manager correspondiente
4. Actualizar bridge en app.js
5. Tests
6. Deploy con feature flag
7. Monitorear errores
8. Eliminar codigo legacy de app.js

#### FASE 3.5: Migrar Utilidades Compartidas (Semana 10-11)

**Utilidades a migrar:**

| De app.js | A static/src/ | LOC aprox |
|-----------|---------------|-----------|
| i18n module | utils/i18n.js | ~200 |
| theme-manager | utils/theme.js | ~150 |
| auth module | utils/auth.js | ~300 |
| escapeHtml | utils/sanitizer.js | ~50 |
| formatters | utils/formatters.js | ~100 |

**Archivo:** `static/src/utils/i18n.js`

```javascript
// Migrar i18n module completo
export const i18n = {
    currentLocale: 'ja',
    translations: {},

    async init() {
        const saved = localStorage.getItem('yukyu-locale');
        this.currentLocale = saved || this.detectBrowserLocale();
        await this.loadTranslations(this.currentLocale);
    },

    t(key, params = {}) {
        let text = this.translations[key] || key;
        for (const [k, v] of Object.entries(params)) {
            text = text.replace(`{${k}}`, v);
        }
        return text;
    },

    // ... rest of i18n functionality
};
```

#### FASE 3.6: Eliminar Legacy (Semana 11-12)

**Prerequisitos:**
- [ ] Todas las paginas migradas
- [ ] Todas las utilidades migradas
- [ ] Tests E2E pasando
- [ ] 2 semanas sin errores en produccion

**Pasos finales:**
```bash
# 1. Backup
cp static/js/app.js basuraa/legacy/app.js.backup

# 2. Crear app.js minimo (solo bootstrap)
cat > static/js/app.js << 'EOF'
/**
 * YuKyu App - Legacy Redirect
 * All functionality moved to static/src/
 */
import YuKyuApp from '/static/src/index.js';

// Auto-initialize
window.__YUKYU_AUTO_INIT__ = true;
YuKyuApp.init();

// Expose for backwards compatibility
window.App = YuKyuApp;
EOF

# 3. Update index.html
# Change script src to type="module"
```

**Verificacion final:**
```bash
npx playwright test tests/e2e/ --headed
# Todas las funcionalidades deben funcionar
```

### 3.4 Matriz de Riesgos - Frontend

| Riesgo | Prob. | Impacto | Mitigacion |
|--------|-------|---------|------------|
| Regresion visual | Alta | Alto | Visual regression tests |
| Perdida de funcionalidad | Media | Alto | Feature parity checklist |
| Performance degradation | Media | Medio | Lighthouse audits |
| Browser compatibility | Baja | Medio | Cross-browser testing |
| Chart library issues | Media | Medio | Mantener mismas versiones |
| i18n broken | Media | Alto | Tests de traducciones |

### 3.5 Checklist Final - Frontend

- [ ] Todas las paginas en static/src/
- [ ] Bridge eliminado (no necesario)
- [ ] app.js reducido a bootstrap
- [ ] Tests E2E 100% pasando
- [ ] Lighthouse score >= 90
- [ ] Todos los idiomas funcionando
- [ ] Dark/Light mode funcionando
- [ ] PWA funcionando
- [ ] No errores en console
- [ ] Documentacion de componentes actualizada

---

## Cronograma Consolidado

```
Semana 1-3:   ROUTES DEPRECATION
  W1: Deprecation middleware + frontend update
  W2: Observacion + tests
  W3: Eliminar v0

Semana 4-9:   ORM MIGRATION
  W4-5: Funciones criticas (save_*, business logic)
  W6-7: Bulk operations + audit
  W8: Feature flag integration
  W9: Testing paralelo + switchover

Semana 4-15:  FRONTEND UNIFICATION (paralelo con ORM)
  W4-6: Dashboard + Employees
  W7-9: LeaveRequests + Analytics
  W10-12: Compliance + Settings + Notifications
  W13-14: Utilities migration
  W15: Legacy elimination
```

```
        W1  W2  W3  W4  W5  W6  W7  W8  W9  W10 W11 W12 W13 W14 W15
ROUTES  [=======]
ORM             [=======================]
FRONTEND            [==========================================]
```

---

## Comandos de Verificacion por Fase

### Quick Health Check
```bash
# Ejecutar despues de cada fase
./scripts/migration-healthcheck.sh
```

**Contenido de `scripts/migration-healthcheck.sh`:**
```bash
#!/bin/bash
set -e

echo "=== YuKyuDATA Migration Health Check ==="

# 1. Tests
echo "Running tests..."
pytest tests/ -v --tb=short -q

# 2. Lint
echo "Running linters..."
npm run lint:js 2>/dev/null || echo "JS lint skipped"

# 3. Server starts
echo "Checking server startup..."
timeout 10 python -c "from main import app; print('Server imports OK')"

# 4. API endpoints
echo "Checking critical endpoints..."
python -c "
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

endpoints = [
    '/api/v1/employees',
    '/api/v1/health',
]

for ep in endpoints:
    r = client.get(ep)
    status = 'OK' if r.status_code in [200, 401] else 'FAIL'
    print(f'  {ep}: {status} ({r.status_code})')
"

echo "=== Health Check Complete ==="
```

### Per-Phase Verification

```bash
# Routes Phase
curl -I http://localhost:8000/api/employees | grep -i deprecation
curl http://localhost:8000/api/v1/employees | jq '.status'

# ORM Phase
USE_ORM=true pytest tests/orm/ -v
python scripts/test_orm_parity.py

# Frontend Phase
npx playwright test tests/e2e/dashboard.spec.ts
npx lighthouse http://localhost:8000 --output=json | jq '.categories.performance.score'
```

---

## Criterios de Rollback

### Cuando hacer rollback:

| Condicion | Accion |
|-----------|--------|
| Error rate > 5% | Rollback inmediato |
| Tests criticos fallan | No deploy, fix primero |
| Performance -20% | Investigar, posible rollback |
| User complaints > 3 | Investigar urgente |

### Como hacer rollback:

**Routes:**
```bash
git revert HEAD  # Si se eliminaron archivos
# O restaurar desde backup
```

**ORM:**
```bash
# En .env
USE_ORM=false
# Reiniciar servidor
```

**Frontend:**
```bash
git checkout HEAD~1 -- static/js/app.js
# O restaurar desde basuraa/legacy/
```

---

## Notas para Humanos

### Decisiones que requieren aprobacion:

1. **Fecha de sunset de v0:** Propuesto 2026-03-01. Confirmar con stakeholders.

2. **ORM switchover:** Confirmar 2 semanas de testing paralelo es suficiente.

3. **Frontend feature flags:** Usar por pagina o global?

4. **Eliminacion de database.py:** Mantener como referencia o eliminar completamente?

### Recursos necesarios:

- 1 desarrollador backend (ORM)
- 1 desarrollador frontend (unificacion)
- QA para testing manual en fases criticas
- Acceso a logs de produccion para monitoreo

### Comunicacion:

- Notificar a usuarios de API sobre deprecacion v0
- Changelog actualizado por fase
- Documentacion tecnica actualizada

---

**Fin del Plan de Migracion**
