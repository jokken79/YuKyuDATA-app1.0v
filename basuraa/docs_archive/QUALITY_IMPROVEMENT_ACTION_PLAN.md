# PLAN DE ACCIÓN PARA MEJORA DE CALIDAD
## YuKyuDATA-app v5.19

**Fecha:** 2026-01-17
**Duración Total Estimada:** 4-6 semanas
**Equipo Requerido:** 1-2 developers

---

## FASE 1: CRÍTICO (Semanas 1-2) - 52 horas

### TAREA 1.1: Refactorizar database.init_db() - 4 horas
**Severidad:** CRÍTICO
**Archivo:** `/home/user/YuKyuDATA-app1.0v/database.py` líneas 80-355

**Cambios:**
- Dividir 276 líneas en 6 funciones (cada una <50 LOC)
- `_create_tables()` - 40 líneas
- `_create_indexes()` - 30 líneas
- `_create_triggers()` - 20 líneas
- `_enable_constraints()` - 10 líneas
- `_create_views()` - 15 líneas
- Mantener `init_db()` como orquestador (10 líneas)

**Pruebas necesarias:**
```bash
pytest tests/test_database_integrity.py::test_init_db_structure -v
sqlite3 yukyu.db ".schema" | wc -l  # Validar tablas creadas
```

---

### TAREA 1.2: Refactorizar services/notifications.py - 8 horas
**Severidad:** CRÍTICO
**Archivo:** `/home/user/YuKyuDATA-app1.0v/services/notifications.py`

**Cambios:**
Refactorizar 4 funciones de notificación (109-121 líneas cada una) usando Template Method:

```python
# Nueva estructura:
class NotificationFactory:
    """Factory para crear notificaciones con template consistente"""

    @staticmethod
    def create_notification(type: str, context: dict) -> Notification:
        if type == 'expiring_days':
            return ExpiringDaysNotification(context)
        elif type == 'compliance_warning':
            return ComplianceWarningNotification(context)
        # ...

class NotificationBase:
    """Template base para todas las notificaciones"""
    def send(self):
        content = self.build_content()
        recipients = self.get_recipients()
        self.store_db(content, recipients)
        self.send_emails(content, recipients)

    def build_content(self):
        raise NotImplementedError

    def get_recipients(self):
        raise NotImplementedError

class ExpiringDaysNotification(NotificationBase):
    def build_content(self):
        # Solo lógica específica - max 20 líneas
        pass
```

**Beneficios:**
- 4 funciones (442 líneas) → Template (80) + 4 concretas (60 líneas c/u)
- Reducción de código: 60%
- Lógica centralizada: 1 lugar

**Pruebas:**
```bash
pytest tests/test_notifications.py -v
# Agregar:
pytest -k "test_expiring_days_content"
pytest -k "test_compliance_warning_recipient_selection"
```

---

### TAREA 1.3: Centralizar Error Handling con Decorator - 4 horas
**Severidad:** CRÍTICO
**Archivos:**
- `/home/user/YuKyuDATA-app1.0v/routes/employees.py` (21 try-except)
- `/home/user/YuKyuDATA-app1.0v/routes/leave_requests.py` (similar)

**Implementar:**

Crear `/home/user/YuKyuDATA-app1.0v/middleware/error_decorator.py`:

```python
from functools import wraps
from typing import Callable, Any, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from utils.logger import logger

def handle_route_errors(endpoint_name: str, default_status: int = 500):
    """Decorator para manejo consistente de errores en endpoints.

    Args:
        endpoint_name: Nombre del endpoint para logging
        default_status: Status code por defecto para errores inesperados
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise  # Re-raise sin cambios
            except ValueError as e:
                logger.warning(f"{endpoint_name}: validation error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except KeyError as e:
                logger.warning(f"{endpoint_name}: missing data: {e}")
                raise HTTPException(status_code=422, detail=f"Missing: {e}")
            except FileNotFoundError as e:
                logger.warning(f"{endpoint_name}: file not found: {e}")
                raise HTTPException(status_code=404, detail=str(e))
            except PermissionError as e:
                logger.warning(f"{endpoint_name}: permission denied: {e}")
                raise HTTPException(status_code=403, detail=str(e))
            except Exception as e:
                logger.error(
                    f"{endpoint_name}: unexpected error",
                    exc_info=True,
                    extra={'error': str(e)}
                )
                raise HTTPException(
                    status_code=default_status,
                    detail="Internal server error"
                )
        return wrapper
    return decorator
```

**Uso:**

```python
from middleware.error_decorator import handle_route_errors

@app.get("/api/employees")
@handle_route_errors("get_employees")
async def get_employees(year: int = Query(...)):
    # Sin try-except, manejado por decorator
    return database.get_employees(year)

@app.post("/api/leave-requests")
@handle_route_errors("create_leave_request", default_status=422)
async def create_leave_request(data: LeaveRequestCreate):
    # Raises ValueError → 400
    # Raises KeyError → 422
    # Otros → 422
    return database.create_leave_request(data)
```

**Cambios requeridos:**

Archivo | Cambios | Líneas Ahorradas
--------|---------|------------------
employees.py | Remove 21 try-except | 126 líneas
leave_requests.py | Remove similar try-except | 80 líneas
compliance.py | Remove similar try-except | 40 líneas

**Pruebas:**
```bash
pytest tests/test_routes_employees.py -v
pytest tests/test_exception_handling.py -v
# Nuevos tests:
pytest -k "test_decorator_catches_value_error"
pytest -k "test_decorator_reraises_http_exception"
```

---

### TAREA 1.4: Fix HTTP Status Codes (118 → 20) - 4 horas
**Severidad:** CRÍTICO
**Impacto:** API correctness, client error handling

**Audit script:**

```bash
grep -r "status_code=500" routes/ | wc -l  # Antes: 118
```

**Cambios sistemáticos:**

| Caso | Actual | Cambiar a | Archivo/Líneas |
|------|--------|-----------|-----------------|
| Missing required field | 500 | 400 | routes/employees.py:156 |
| Invalid input format | 500 | 422 | routes/leave_requests.py:213 |
| Resource not found | 500 | 404 | routes/yukyu.py:145 |
| Unauthorized | 500 | 401 | routes/auth.py:89 |
| Forbidden | 500 | 403 | routes/compliance.py:112 |

**Script de automatización:**

```python
# scripts/fix_status_codes.py
import re
import sys
from pathlib import Path

def fix_file(filepath):
    content = Path(filepath).read_text()

    # Reemplazos básicos
    replacements = [
        (r'status_code=500.*?KeyError', 'status_code=400'),
        (r'status_code=500.*?ValueError', 'status_code=422'),
        (r'status_code=500.*?FileNotFoundError', 'status_code=404'),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    Path(filepath).write_text(content)
    print(f"Fixed {filepath}")

if __name__ == '__main__':
    for f in Path('routes').glob('*.py'):
        fix_file(f)
```

**Validación:**
```bash
# Después de cambios:
grep -r "status_code=500" routes/ | wc -l  # Después: ~20 (solo genuinos)

# Verificar que 400/422 aumentaron:
grep -r "status_code=400" routes/ | wc -l
grep -r "status_code=422" routes/ | wc -l
```

---

### TAREA 1.5: Fix JavaScript Memory Leak - 2 horas
**Severidad:** CRÍTICO
**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/js/app.js`

**Problema:** 31 addEventListener(), 0 removeEventListener()

**Solución:**

```javascript
// Paso 1: Refactorizar App a clase
class AppManager {
    constructor() {
        this.state = { /* ... */ };
        this.listeners = new Map();  // Rastrear listeners
    }

    init() {
        this._bindEvent('click', this.handleClick);
        this._bindEvent('change', this.handleChange);
        this._bindEvent('submit', this.handleSubmit);
        // ... etc (31 en total)
    }

    _bindEvent(eventType, handler) {
        const bound = handler.bind(this);
        document.addEventListener(eventType, bound);

        // Guardar para cleanup
        const key = `${eventType}:${handler.name}`;
        this.listeners.set(key, { eventType, handler: bound });
    }

    destroy() {
        // Limpiar listeners
        for (const { eventType, handler } of this.listeners.values()) {
            document.removeEventListener(eventType, handler);
        }
        this.listeners.clear();

        // Limpiar state
        this.state = null;

        // Limpiar charts si existen
        if (this.charts) {
            Object.values(this.charts).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            });
        }
    }

    // Handlers...
    handleClick(e) { /* ... */ }
    handleChange(e) { /* ... */ }
}

// Uso global
window.app = new AppManager();
window.app.init();

// Cuando cambiar vista:
window.app.destroy();
window.app = new AppManager();
window.app.init();
```

**Validación:**

```bash
# Chrome DevTools → Memory → Heap Snapshot
# Antes: listeners se acumulan
# Después: listeners se limpian

# Test de memory leak:
npx playwright test tests/e2e/memory-leak.spec.js
```

**Nuevo test:** `tests/e2e/memory-leak.spec.js`

```javascript
test('should not accumulate event listeners', async ({ page }) => {
    // Navegar múltiples veces
    for (let i = 0; i < 10; i++) {
        await page.goto('/');
        await page.click('a[href="#employees"]');
        await page.waitForTimeout(100);
    }

    // Verificar que no hay memory leak
    const metrics = await page.metrics();
    expect(metrics.JSHeapUsedSize).toBeLessThan(50 * 1024 * 1024); // <50MB
});
```

---

### TAREA 1.6: Add Type Hints Completos (main.py) - 4 horas
**Severidad:** ALTO
**Archivo:** `/home/user/YuKyuDATA-app1.0v/main.py` (16 funciones sin return type)

**Ejemplos:**

```python
# Antes:
def audit_action(action: str, entity_type: str, get_entity_id=None, get_old_value=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # ...

# Después:
from typing import Callable, Optional, Awaitable, Any, Union

def audit_action(
    action: str,
    entity_type: str,
    get_entity_id: Optional[Callable[[tuple, dict], str]] = None,
    get_old_value: Optional[Callable[[tuple, dict], Union[dict, Any]]] = None
) -> Callable:
    """Decorator para registrar acciones en audit log.

    Args:
        action: Tipo de acción (CREATE, UPDATE, DELETE, etc.)
        entity_type: Tipo de entidad
        get_entity_id: Función para extraer entity_id
        get_old_value: Función para obtener valor anterior

    Returns:
        Decorated async function
    """
    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # ...
            return result
        return wrapper
    return decorator
```

**Herramienta para ayudar:**
```bash
# Instalar mypy
pip install mypy

# Ejecutar en main.py
mypy main.py --no-error-summary 2>&1 | head -20

# Esto mostrará dónde faltan tipos
```

---

### TAREA 1.7: Add Docstrings Completos - 4 horas
**Severidad:** ALTO
**Funciones:** 14 sin docstring (11 en main.py, 2 en database.py, 1 en excel_service.py)

**Template de docstring:**

```python
def parse_date(value: Any) -> Optional[date]:
    """Parse date from various input formats.

    Supports datetime.date objects, ISO format strings (YYYY-MM-DD),
    and numeric formats (Excel serial dates).

    Args:
        value: Date in one of supported formats

    Returns:
        datetime.date object if parsing succeeds, None if value is None,
        raises ValueError if format is unrecognizable

    Raises:
        ValueError: If date format cannot be parsed
        TypeError: If value type is unsupported

    Examples:
        >>> parse_date(datetime.date(2025, 1, 17))
        datetime.date(2025, 1, 17)

        >>> parse_date("2025-01-17")
        datetime.date(2025, 1, 17)

        >>> parse_date(None)
        None

        >>> parse_date("invalid")
        Traceback (most recent call last):
            ...
        ValueError: Cannot parse date from 'invalid'
    """
    if value is None:
        return None

    if isinstance(value, date):
        return value

    # ... resto de implementación
```

---

## FASE 2: ALTO (Semanas 3-4) - 48 horas

### TAREA 2.1: Refactorizar services/reports.py - 8 horas
**Severidad:** ALTO
**Archivo:** `/home/user/YuKyuDATA-app1.0v/services/reports.py` (5 funciones >100 LOC)

**Usar Factory + Template Pattern:**

```python
class ReportGenerator:
    """Base class para todos los tipos de reportes"""

    def generate(self) -> bytes:
        """Template method"""
        self._validate_input()
        data = self._collect_data()
        formatted = self._format_data(data)
        return self._render_pdf(formatted)

    def _validate_input(self):
        raise NotImplementedError

    def _collect_data(self):
        raise NotImplementedError

    def _format_data(self, data):
        raise NotImplementedError

    def _render_pdf(self, formatted_data):
        # Implementación común
        pass

class MonthlyReportGenerator(ReportGenerator):
    def _validate_input(self):
        # Solo validación mensual
        pass

class AnnualReportGenerator(ReportGenerator):
    def _validate_input(self):
        # Solo validación anual
        pass

# Uso:
report = MonthlyReportGenerator(year=2025, month=1)
pdf_bytes = report.generate()
```

---

### TAREA 2.2: Excel Parsing - Eliminar Duplicación - 6 horas
**Severidad:** ALTO
**Archivo:** `/home/user/YuKyuDATA-app1.0v/services/excel_service.py` (3 funciones casi idénticas)

**Consolidar:**
- `parse_yukyu_usage_details` (102 líneas)
- `parse_yukyu_usage_details_enhanced` (164 líneas)
- Parsing genérico en `parse_excel_file` (143 líneas)

```python
def _parse_usage_details(
    sheet: Worksheet,
    config: ExcelParseConfig,
    enhanced: bool = False
) -> List[UsageDetail]:
    """Unified usage details parser.

    Soporta both standard y enhanced parsing modes.
    """
    if enhanced:
        # Lógica enhanced (20 líneas)
        pass
    else:
        # Lógica standard (15 líneas)
        pass
    return details
```

---

### TAREA 2.3: Add Agent Functional Tests - 12 horas
**Severidad:** ALTO
**Coverage actual:** ~5% (solo imports)

**Crear tests en `/home/user/YuKyuDATA-app1.0v/tests/test_agents_functional.py`:**

```python
import pytest
from agents.compliance import ComplianceAgent
from agents.memory import MemoryAgent
from agents.orchestrator import OrchestratorAgent

class TestComplianceAgent:
    """Test ComplianceAgent business logic"""

    def test_check_5day_compliance_passes(self):
        """Verify 5-day rule compliance detection"""
        agent = ComplianceAgent()
        result = agent.check_5day_compliance(year=2025)

        assert isinstance(result, dict)
        assert 'compliant' in result
        assert 'employees_compliant' in result
        assert 'warnings' in result

    def test_check_5day_compliance_detects_violations(self):
        """Verify detection of 5-day rule violations"""
        agent = ComplianceAgent()
        # ... setup employee with <5 days used ...

        result = agent.check_5day_compliance(year=2025)
        assert not result['compliant']
        assert len(result['warnings']) > 0

class TestMemoryAgent:
    """Test MemoryAgent persistence"""

    def test_store_and_retrieve_context(self):
        """Verify context storage and retrieval"""
        agent = MemoryAgent()

        context = {
            'session_id': 'test_123',
            'timestamp': datetime.now(),
            'data': {'key': 'value'}
        }

        agent.store_session_context(context)
        retrieved = agent.get_session_context('test_123')

        assert retrieved['data']['key'] == 'value'
```

---

### TAREA 2.4: Add Middleware Tests - 8 horas
**Severidad:** ALTO
**Coverage actual:** ~30%

```python
# tests/test_middleware_csrf.py
import pytest
from starlette.testclient import TestClient
from main import app

client = TestClient(app)

def test_csrf_token_generated():
    """Verify CSRF token in response"""
    response = client.get("/")
    assert "csrf_token" in response.cookies or "X-CSRF-Token" in response.headers

def test_csrf_protection_on_post():
    """Verify CSRF protection blocks invalid requests"""
    response = client.post("/api/employees", json={"name": "test"})
    # Sin CSRF token debe fallar
    assert response.status_code in [403, 422]

def test_csrf_protection_accepts_valid_token():
    """Verify valid CSRF token is accepted"""
    # Obtener token
    r1 = client.get("/")
    token = extract_csrf_token(r1)

    # Usar token
    r2 = client.post(
        "/api/employees",
        json={"name": "test"},
        headers={"X-CSRF-Token": token}
    )
    assert r2.status_code != 403
```

---

### TAREA 2.5: Refactor App Singleton a Clase - 12 horas
**Severidad:** ALTO
**Archivo:** `/home/user/YuKyuDATA-app1.0v/static/js/app.js` (7,091 líneas)

**Transformar:**

```javascript
// Antes:
const App = {
    state: { /* ... */ },
    init() { /* ... */ },
    showDashboard() { /* ... */ },
    // ... 200+ métodos directos
};

// Después:
class AppManager {
    constructor() {
        this.state = { /* ... */ };
        this.listeners = new Map();
    }

    init() {
        this._bindEvents();
        this._loadInitialData();
    }

    showDashboard() {
        this._clearView();
        this._renderDashboard();
    }

    destroy() {
        this._removeAllListeners();
        this.state = null;
    }

    _bindEvents() { /* ... */ }
    _clearView() { /* ... */ }
    _renderDashboard() { /* ... */ }
    _removeAllListeners() { /* ... */ }
}

// Global instance
window.appManager = new AppManager();
```

**Beneficios:**
- Testeable (mock constructor)
- Multiple instancias posibles
- Lifecycle manejable (destroy)
- Mejor memory management

---

## FASE 3: MEDIO (Semanas 5-6) - 32 horas

### TAREA 3.1: N+1 Query Fix - 4 horas
**Archivo:** `/home/user/YuKyuDATA-app1.0v/routes/employees.py` línea ~920

```python
# Antes (N+1):
employees = database.get_employees(year)
for emp in employees:
    balance = database.get_balance(emp['employee_num'])  # Query por cada uno
    emp['balance'] = balance

# Después (optimizado):
employees = database.get_employees_with_balance(year)
# O usar JOIN en SQL directamente
```

---

### TAREA 3.2: Database Indexes - 4 horas
**Archivo:** `/home/user/YuKyuDATA-app1.0v/database.py`

```python
# Agregar en _create_indexes():
indexes = [
    "CREATE INDEX IF NOT EXISTS idx_leave_requests_emp_year ON leave_requests(employee_num, year)",
    "CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status)",
    "CREATE INDEX IF NOT EXISTS idx_yukyu_usage_emp_year ON yukyu_usage_details(employee_num, year)",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id)",
]
```

---

### TAREA 3.3: Add Frontend Component Tests - 8 horas
**Cobertura actual:** 5/21 componentes

```bash
# Crear tests para:
# - Alert.js (toast notifications)
# - Form.js (validation, submission)
# - Table.js (sorting, filtering, pagination)
# - DatePicker.js (date selection)
# - Modal.js (open/close, actions)
# - Select.js (search, multi-select)
# - Loader.js (skeleton, spinner)
```

---

### TAREA 3.4: Add ESLint + Prettier - 4 horas
**Objetivo:** Automated code formatting

```json
// .eslintrc.json
{
  "env": {
    "browser": true,
    "es2021": true
  },
  "extends": ["eslint:recommended"],
  "parserOptions": {
    "ecmaVersion": "latest"
  },
  "rules": {
    "no-unused-vars": "warn",
    "no-console": "warn",
    "prefer-const": "error",
    "no-var": "error",
    "eqeqeq": "error"
  }
}
```

```bash
# Agregar a package.json scripts:
"lint": "eslint static/src/**/*.js",
"lint:fix": "eslint static/src/**/*.js --fix",
"format": "prettier --write static/src/**/*.js"
```

---

### TAREA 3.5: Add Python Linting - 4 horas
**Setup mypy, flake8, black**

```bash
# Instalar
pip install mypy flake8 black isort

# Ejecutar
mypy main.py database.py routes/ services/
flake8 main.py database.py --max-line-length=120
black --check main.py
isort --check-only .

# Agregar a GitHub Actions
```

---

### TAREA 3.6: Documentation Improvements - 8 horas

**Crear:**

1. `/home/user/YuKyuDATA-app1.0v/docs/ADR/` - Architecture Decision Records
   - ADR-001-Database-Schema
   - ADR-002-Authentication-Strategy
   - ADR-003-Frontend-Architecture

2. `/home/user/YuKyuDATA-app1.0v/docs/RUNBOOKS/` - Operational guides
   - Setup.md
   - Deployment.md
   - Troubleshooting.md
   - Backup-Recovery.md

3. Update `/home/user/YuKyuDATA-app1.0v/README.md` con líneas de código actuales

---

## TIMELINE VISUALIZACIÓN

```
Week 1          Week 2          Week 3          Week 4          Week 5-6
├─ 1.1,1.2  ├─ 1.4,1.5  ├─ 2.1,2.2  ├─ 2.3,2.4  ├─ 3.1-3.6
├─ 1.3      ├─ 1.6,1.7  ├─ 2.5      │           └─ Buffer
│           │           │           │
Init+       Error       Reports+    Agents+     Misc+
Notifs      Fix         Excel       Refactor    Polish

Fase 1 CRÍTICO: 52h
Fase 2 ALTO: 48h
Fase 3 MEDIO: 32h
─────────────────────
Total: 132 horas (~4-6 semanas)
```

---

## CRITERIOS DE ACEPTACIÓN

### Fase 1 Complete

```bash
✓ Zero functions >100 LOC (database, notifications, reports)
✓ try-except duplicación eliminada (21 → 0)
✓ HTTP status codes corregidos (118 → <20)
✓ Memory leak JavaScript removido (31 listeners cleaned)
✓ Type hints en main.py 100%
✓ Docstrings en funciones críticas 100%
✓ All tests passing (62/62)
✓ Code quality score: 7.0/10
```

### Fase 2 Complete

```bash
✓ Reports refactorizado (5 → 1 + templates)
✓ Excel parsing sin duplicación
✓ Agent tests: coverage >60%
✓ Middleware tests: coverage >60%
✓ App refactored a clase
✓ All tests passing (100+)
✓ Code quality score: 8.0/10
```

### Fase 3 Complete

```bash
✓ N+1 queries optimizadas
✓ Database indexes creados
✓ Frontend components >80% coverage
✓ ESLint + Prettier configurado
✓ mypy + flake8 en CI/CD
✓ Documentation actualizada
✓ Code quality score: 8.5+/10
```

---

## ESTIMACIÓN DE RECURSOS

| Recurso | Fase 1 | Fase 2 | Fase 3 | Total |
|---------|--------|--------|--------|-------|
| **Dev 1 (Senior)** | 26h | 30h | 20h | 76h |
| **Dev 2 (Junior, si aplica)** | 26h | 18h | 12h | 56h |
| **QA/Testing** | 8h | 12h | 8h | 28h |
| **Total Horas** | 52h | 48h | 32h | **132h** |
| **Duración (1 dev, part-time)** | 2 weeks | 2 weeks | 2 weeks | **6 weeks** |
| **Duración (2 devs, full-time)** | 1 week | 1 week | 1 week | **3 weeks** |

---

## SUCCESS METRICS

**Before:**
```
Quality Score: 5.75/10
Technical Debt: 100 points
Code Smells: 15+
```

**After:**
```
Quality Score: 8.5+/10
Technical Debt: 20-30 points
Code Smells: <3
```

**Medición:**

```bash
# Run quarterly
python scripts/quality-check.py

# Generates report:
# - Lines of code
# - Functions >100 LOC count
# - Type hint coverage %
# - Docstring coverage %
# - Test coverage %
# - Code smell count
```

---

## PRÓXIMOS PASOS

1. **Obtener aprobación** para esta plan
2. **Priorizar tareas** según urgencia del equipo
3. **Asignar recursos**
4. **Crear GitHub issues** por tarea
5. **Setup CI/CD checks** para evitar regresión
6. **Weekly status** reuniones
7. **Post-Phase retrospectives**

---

**Generado:** 2026-01-17
**Aprobado por:** [Pending]
**Comenzar:** [Pending]
