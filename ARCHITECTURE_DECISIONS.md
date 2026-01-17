# ADR (Architecture Decision Records) - YuKyuDATA

Decisiones arquitectónicas clave y alternativas evaluadas.

---

## ADR-001: Schema de Base de Datos - ID Compuesto vs Surrogate Key

**Status:** 🔴 REVOKED (Debe cambiar)
**Date:** 2026-01-17
**Author:** Claude DevOps Audit

### Contexto
La tabla `employees` usa ID compuesto `{employee_num}_{year}` como primary key.

### Problema
- ❌ Previene sharding horizontal
- ❌ Imposibilita distribución geográfica
- ❌ Dificulta particionamiento
- ❌ Aumenta complejidad de queries

### Decisión Anterior
```python
CREATE TABLE employees (
    id TEXT PRIMARY KEY,  # employee_num_year
    employee_num TEXT,
    year INTEGER
)
```

### Nueva Decisión (PROPUESTA)
```python
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_num TEXT NOT NULL,
    year INTEGER NOT NULL,
    UNIQUE(employee_num, year),
    FOREIGN KEY (employee_num) REFERENCES employee_master(employee_num)
)

-- Índices
CREATE INDEX idx_emp_year ON employees(employee_num, year);
CREATE INDEX idx_year ON employees(year);
```

### Alternativas Consideradas

| Opción | Pros | Cons | Score |
|--------|------|------|-------|
| **1. Keep {emp}_{year}** | ✓ No cambios | ✗ No escalable ✗ Inmóvil | 2/10 |
| **2. Surrogate INT (ELEGIDA)** | ✓ Escalable ✓ Estándar ✓ Shardeable | ✗ Migración 1 semana | 9/10 |
| **3. UUID** | ✓ Distribuido | ✗ Mayor tamaño índices | 6/10 |
| **4. ULID** | ✓ Temporal + distribuido | ✗ Menos familiar | 7/10 |

### Impacto
- **Database:** 1 semana migración + backfill
- **Code:** Cambios en 150+ queries
- **API:** Endpoints id permanecen compatibles (UUID en response)
- **Breaking:** No, si se expone UUID en API

### Plan de Migración
```sql
-- Step 1: Create new table
CREATE TABLE employees_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_num TEXT NOT NULL,
    year INTEGER NOT NULL,
    ... todas las otras columnas ...
);

-- Step 2: Migrate data
INSERT INTO employees_new
SELECT ROWID, employee_num, year, ... FROM employees;

-- Step 3: Create constraints
ALTER TABLE employees_new ADD UNIQUE(employee_num, year);
CREATE INDEX idx_emp_year ON employees_new(employee_num, year);

-- Step 4: Drop old, rename new
DROP TABLE employees;
ALTER TABLE employees_new RENAME TO employees;

-- Step 5: Update auto_increment counter
UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM employees);
```

### Riesgos
- 🟠 Downtime: ~30 min (si base de datos pequeña)
- 🟠 Necesita backup antes
- 🟠 Queries rompen si no se actualizan

### Decisión: ✅ ACEPTADA
**Implementar en Sprint 1, Week 1-2**

---

## ADR-002: Data Access Layer - Repository vs Direct DB Calls

**Status:** 🟡 PENDING
**Date:** 2026-01-17

### Contexto
Rutas importan `database` directamente y llaman funciones como:
```python
database.get_employees(year)
database.create_leave_request(...)
```

### Problema
- ❌ Rutas tightly coupled a implementation de database
- ❌ No testeable sin base de datos real
- ❌ No se puede cambiar de SQLite a PostgreSQL fácilmente
- ❌ Lógica de negocio dispersa

### Decisión Actual
```python
# routes/employees.py
@router.get("/employees")
async def get_employees(year: int):
    return database.get_employees(year)  # Direct call
```

### Nueva Decisión (PROPUESTA)
```python
# repositories/interfaces.py
from abc import ABC, abstractmethod

class EmployeeRepository(ABC):
    @abstractmethod
    async def get_by_year(self, year: int) -> List[Employee]: pass

    @abstractmethod
    async def get_by_number(self, emp_num: str, year: int) -> Optional[Employee]: pass

# repositories/sqlite_repository.py
class SQLiteEmployeeRepository(EmployeeRepository):
    def __init__(self, db: Database):
        self.db = db

    async def get_by_year(self, year: int):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM employees WHERE year = ?", (year,))
            return [Employee(**row) for row in c.fetchall()]

# routes/employees.py
@router.get("/employees")
async def get_employees(
    year: int,
    repo: EmployeeRepository = Depends(get_employee_repository)
):
    return await repo.get_by_year(year)
```

### Alternativas Consideradas

| Opción | Pros | Cons | Score |
|--------|------|------|-------|
| **1. Direct database** | ✓ Simple | ✗ Tightly coupled ✗ No testeable | 3/10 |
| **2. Repository (ELEGIDA)** | ✓ Testeable ✓ Swappable ✓ DI-friendly | ✗ 20% código extra | 9/10 |
| **3. Service Layer** | ✓ Business logic abstracted | ✗ Más verboso ✗ Overkill | 7/10 |
| **4. DAO Pattern** | ✓ Familiar a OOP devs | ✗ Tipo Java, no Python-ic | 5/10 |

### Impacto
- **Code:** ~2,000 líneas nuevas (repositories/)
- **Routes:** Cambios mínimos (solo imports)
- **Tests:** Mucho más fácil
- **Migration:** Gradual (ruta por ruta)

### Beneficios Concretos

```python
# Before: Difícil de testear
def test_get_employees():
    # Requiere base de datos real
    response = client.get("/api/employees?year=2025")
    assert response.status_code == 200

# After: Muy fácil
def test_get_employees(mock_repo):
    mock_repo.get_by_year.return_value = [
        Employee(employee_num="001", name="Taro", ...),
        Employee(employee_num="002", name="Hanako", ...)
    ]
    response = client.get("/api/employees?year=2025")
    assert response.status_code == 200
    assert len(response.json()['data']) == 2
```

### Plan de Implementación
1. Create `repositories/interfaces.py` (abstract base classes)
2. Create `repositories/sqlite_impl.py` (concrete SQLite)
3. Refactor routes one by one
4. Add tests para cada repositorio
5. Create `routes/dependencies.py` con DI setup

### Riesgos
- 🟡 Requiere cambios en 20 rutas
- 🟡 Periodo de transición con ambos patrones

### Decisión: ✅ ACEPTADA
**Implementar gradualmente, Sprint 1-2**

---

## ADR-003: Frontend Architecture - Consolidar Legacy vs Moderno

**Status:** 🟡 IN PROGRESS
**Date:** 2026-01-17

### Contexto
Dos sistemas frontend en paralelo:
- `static/js/app.js` (7,091 líneas) - Legacy, estable
- `static/src/` (13,874 líneas) - Moderno, componentes

Total: ~21,000 líneas de código duplicado

### Problema
- ❌ Mantenimiento duplicado
- ❌ Inconsistencia UX
- ❌ Bundle size 2x más grande
- ❌ Testing duplicado

### Decisión Actual
Coexistencia con `legacy-adapter.js` como puente

### Nueva Decisión (PROPUESTA)
Deprecate legacy, migrar a static/src/ en 3 fases

### Alternativas Consideradas

| Opción | Pros | Cons | Score |
|--------|------|------|-------|
| **1. Keep both (actual)** | ✓ No breaking changes | ✗ 2x mantenimiento ✗ Confusión | 4/10 |
| **2. Consolidate (ELEGIDA)** | ✓ Single codebase ✓ Mantenible | ✗ 2 semanas trabajo | 9/10 |
| **3. Rewrite from scratch** | ✓ Modern tech (Vue/React) | ✗ 1 mes trabajo ✗ Riesgo | 5/10 |
| **4. Hybrid (Vue + legacy)** | ✓ Gradual | ✗ Dependency hell | 3/10 |

### Plan de Transición (3 Phases, 3 semanas)

**PHASE 1: Feature Parity (Week 1)**
- Auditar todas las features de legacy
- Completar features faltantes en static/src/
- ~80% dev time aquí

**PHASE 2: Migration (Week 2)**
- Deprecate legacy (console.warn)
- Rewrite legacy usando componentes de static/src/
- Redirect /legacy → /static/src/

**PHASE 3: Cleanup (Week 3)**
- Remove legacy app.js
- Bundle optimization
- Performance testing

### Bundle Size Impact

```
BEFORE:
├── app.js (7 KB)
├── modules/ (2.5 KB)
└── src/ (5.5 KB)
Total: 15 KB

AFTER (with webpack):
├── bundle.HASH.js (6 KB)
├── vendors.HASH.js (1.2 KB)
└── components.HASH.js (1.8 KB)
Total: 9 KB

Savings: 40% reduction
```

### Riesgos
- 🟡 Users habituados a legacy UI
- 🟡 Bugs durante migration
- 🟠 Requiere E2E testing exhaustivo

### Mitigation
- Feature flag para gradual rollout
- A/B testing (10% usuarios a new UI)
- Fallback button "Use Legacy UI"

### Decisión: ✅ ACEPTADA
**Implementar Sprint 2, Week 5-8**

---

## ADR-004: Database Migrations - Alembic vs Manual Scripts

**Status:** 🟡 PROPOSED
**Date:** 2026-01-17

### Contexto
Actualmente NO hay migrations formales. Schema se crea en `database.py` con SQL inline.

### Problema
- ❌ Sin versionado de schema
- ❌ Imposible reproducir schema histórico
- ❌ Rollback manual = error-prone
- ❌ Multi-environment (dev/staging/prod) no sincronizados

### Decisión Actual
```python
# database.py
def init_db():
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (...)''')  # Inline SQL
    c.execute('''CREATE INDEX IF NOT EXISTS idx_usage ... ''')   # Más inline SQL
```

### Nueva Decisión (PROPUESTA)
Implementar Alembic para migrations formales

```bash
# Setup
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add employees table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Estructura Alembic

```
alembic/
├── versions/
│   ├── 001_initial_schema.py        # Create tables
│   ├── 002_add_audit_log.py         # Add audit table
│   ├── 003_fix_id_schema.py         # FIX: Change ID compuesto → surrogate
│   └── 004_add_indexes.py           # Add indexes
├── env.py                            # Alembic environment
├── script.py.mako                    # Migration template
└── alembic.ini                       # Configuration
```

### Ejemplo Migration

```python
# alembic/versions/003_fix_id_schema.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Change ID from composite string to surrogate int"""
    op.create_table('employees_new',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('employee_num', sa.String(10), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        # ... other columns ...
        sa.UniqueConstraint('employee_num', 'year')
    )

    # Migrate data
    op.execute('''
        INSERT INTO employees_new
        SELECT ROWID, employee_num, year, ... FROM employees
    ''')

    # Drop old table
    op.drop_table('employees')
    op.rename_table('employees_new', 'employees')

def downgrade():
    """Revert to composite ID"""
    op.create_table('employees_old',
        sa.Column('id', sa.String(20), primary_key=True),
        # ...
    )
    # ... reverse migration logic ...
```

### Alternativas

| Opción | Pros | Cons | Score |
|--------|------|------|-------|
| **1. Manual scripts** | ✓ Simple ✓ Control total | ✗ Error-prone ✗ No tracking | 3/10 |
| **2. Alembic (ELEGIDA)** | ✓ Standard ✓ Reversible ✓ Tracked | ✗ Learning curve | 9/10 |
| **3. Flyway** | ✓ Multiplatform | ✗ Java-based, overkill | 6/10 |
| **4. SQLAlchemy DDL** | ✓ Pythonic | ✗ No downgrade support | 5/10 |

### Impacto
- **Setup:** 4 horas
- **First migration:** 8 horas (escribir schema existente)
- **Ongoing:** 30 min per migration

### Decisión: ✅ ACEPTADA
**Implementar Sprint 1, Week 3**

---

## ADR-005: Agent System - Parte de App vs Herramienta Separada

**Status:** 🟡 PROPOSED
**Date:** 2026-01-17

### Contexto
Sistema de 13 agentes (11,307 líneas) en `agents/`:
- ComplianceAgent, SecurityAgent, PerformanceAgent, etc.
- OrchestratorAgent coordina
- MemoryAgent persiste aprendizajes

**Pregunta:** ¿Deben estar en la aplicación principal?

### Problema
- ❌ 11,307 líneas sin usar en rutas
- ❌ No se invocan en endpoints
- ❌ Parecen ser herramientas de desarrollo, no features
- ❌ Agregan complejidad sin valor en producción
- ❌ Sin tests

### Decisión Actual
Agentes viven en `agents/` dentro de app principal

### Nueva Decisión (PROPUESTA)
Mover agentes a **CLI tool separado**: `yukyu-cli`

```bash
# Usar en desarrollo/análisis:
yukyu-cli analyze --full              # Full analysis
yukyu-cli compliance --year 2025      # 5-day compliance
yukyu-cli security --audit            # Security audit
yukyu-cli performance --profile        # Profile queries
```

### Estructura Nueva

```
yukyu-cli/ (Nuevo repositorio)
├── commands/
│   ├── analyze.py         # Full analysis
│   ├── compliance.py      # Compliance checking
│   ├── security.py        # Security audit
│   ├── performance.py     # Performance profiling
│   └── ...
├── agents/                # Move from main repo
├── main.py                # CLI entrypoint
└── setup.py               # PyPI package

# Instalar:
pip install yukyu-cli
yukyu-cli help

# Usar:
yukyu-cli compliance --database /path/to/yukyu.db --year 2025
```

### Beneficios

```python
# BEFORE (embedding en app):
from agents import get_compliance
@router.get("/api/agents/compliance")
async def check_compliance(year: int):
    agent = get_compliance()
    return agent.check_5day_compliance(year)

# AFTER (CLI tool):
$ yukyu-cli compliance --year 2025
┌─────────────────────────────────────────┐
│ 5-Day Compliance Check (2025)          │
├─────────────────────────────────────────┤
│ ✅ Compliant employees:   475/500       │
│ ⚠️  Warning (< 5 days):    20            │
│ ❌ Non-compliant:          5             │
└─────────────────────────────────────────┘

# Salida también a JSON:
$ yukyu-cli compliance --year 2025 --format json | jq
{
  "compliant_count": 475,
  "warning_count": 20,
  "non_compliant_count": 5
}
```

### Alternativas

| Opción | Pros | Cons | Score |
|--------|------|------|-------|
| **1. Keep in app** | ✓ Centralizado | ✗ Bloat ✗ Unused | 3/10 |
| **2. CLI tool (ELEGIDA)** | ✓ Separación ✓ Reutilizable | ✗ Otro repo | 9/10 |
| **3. Lambda functions** | ✓ Serverless | ✗ AWS-specific | 6/10 |
| **4. Scheduled jobs** | ✓ Automated | ✗ Less flexible | 5/10 |

### Migration Plan
1. Create `yukyu-cli` repository
2. Move `agents/` to new repo
3. Keep `memory.py` en app principal (para logging)
4. Update imports en app
5. Publish to PyPI

### Impacto
- **App size:** -11,307 líneas (32% reduction)
- **Bundle:** No cambio (no es parte de static/)
- **Deployment:** Misma imagen Docker (install extra package)

### Riesgos
- 🟡 Requiere mantener dos repos
- 🟡 CLI necesita documentación

### Decisión: ✅ ACEPTADA
**Implementar Sprint 1, Week 4**

---

## ADR-006: ORM Selection - SQLAlchemy vs Raw SQL vs Tortoise ORM

**Status:** 🟡 DEFERRED
**Date:** 2026-01-17

### Contexto
Actualmente usando raw SQL. Considerar ORM para futuro escalado.

### Problema
- ⚠️ Raw SQL error-prone a escala
- ⚠️ Sin type safety
- ⚠️ N+1 queries posibles
- ⚠️ Migraciones manuales

### Alternativas

| Aspecto | Raw SQL | SQLAlchemy | Tortoise | Beanie |
|---------|---------|-----------|----------|--------|
| **Async** | Parcial | ✅ v2.0+ | ✅ Nativo | ✅ Nativo |
| **Type safety** | ❌ | ✅ | ✅ | ✅ |
| **Migrations** | Manual | ✅ Alembic | ✅ Aerich | ✅ Aerich |
| **Learning curve** | Low | High | Medium | Medium |
| **Performance** | Best | Good | Good | Good |
| **Popular** | N/A | ✅ Very | ✅ Growing | 🟡 Niche |
| **Score** | 5/10 | 9/10 | 8/10 | 6/10 |

### Recomendación
**SQLAlchemy 2.0+ con async** (cuando migrar)

```python
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, Session

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    employee_num = Column(String(10), unique=True)
    name = Column(String(100))
    year = Column(Integer)

# Async engine
engine = create_async_engine("sqlite+aiosqlite:///./yukyu.db")

# Usage
async def get_employees(session: AsyncSession, year: int):
    stmt = select(Employee).where(Employee.year == year)
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Cuándo Migrar
- **Now:** Solo si hay recursos dedicados
- **Next 6 months:** Plan migration
- **Next year:** Implement in phases

### Decisión: 📋 DEFERRED
**Evaluar después de Sprint 2 (Week 8)**

---

## ADR-007: Caching Strategy - TTL vs Event-Driven

**Status:** 🟡 PROPOSED
**Date:** 2026-01-17

### Contexto
Cache actual: TTL fijo (300s) sin invalidación predictiva

### Problema
- ⚠️ Stale data hasta 5 minutos
- ⚠️ Sin invalidación en updates
- ⚠️ Sin cache warming
- ⚠️ Sin métricas hit/miss

### Decisión Actual
```python
@cached(ttl=300)
def get_employees(year):
    return database.get_employees(year)
```

### Nueva Decisión (PROPUESTA)
Hybrid: TTL + Event-driven invalidation

```python
from services.caching import Cache, CacheInvalidationEvent

# Decorator con invalidación automática
@cached(ttl=300, invalidate_on=[
    CacheInvalidationEvent.EMPLOYEE_UPDATED,
    CacheInvalidationEvent.EMPLOYEE_DELETED
])
def get_employees(year):
    return database.get_employees(year)

# En rutas
@router.put("/employees/{emp_num}/{year}")
async def update_employee(emp_num: str, year: int, data: EmployeeUpdate):
    result = database.update_employee(emp_num, year, data)

    # Automático: cache.invalidate("employees:2025")
    event_bus.emit(CacheInvalidationEvent.EMPLOYEE_UPDATED, {
        'emp_num': emp_num,
        'year': year
    })

    return result

# Cache warming (before expiry)
@scheduler.scheduled_job('cron', minute='*/4')  # Every 4.5 min
async def warm_cache():
    for year in get_available_years():
        get_employees(year)  # Pre-populate cache
```

### Alternativas

| Opción | Pros | Cons | Score |
|--------|------|------|-------|
| **1. TTL only (actual)** | ✓ Simple | ✗ Stale data | 4/10 |
| **2. Event-driven (ELEGIDA)** | ✓ Fresh ✓ Efficient | ✗ Más código | 8/10 |
| **3. Redis cache** | ✓ Distributed | ✗ Extra infra | 7/10 |
| **4. Write-through** | ✓ Always fresh | ✗ Write penalty | 6/10 |

### Impacto
- **Code:** +200-300 líneas
- **Dependency:** Redis opcional (fallback memory)
- **Performance:** 20-30% faster

### Decisión: ✅ ACEPTADA
**Implementar Sprint 3, Week 9**

---

## ADR-008: Monitoreo - Prometheus vs CloudWatch vs DataDog

**Status:** 🟡 PROPOSED
**Date:** 2026-01-17

### Contexto
Actualmente sin monitoreo/observabilidad en producción.

### Alternativas

| Aspecto | Prometheus | CloudWatch | DataDog | ELK |
|---------|-----------|-----------|---------|-----|
| **Self-hosted** | ✅ | ❌ | ❌ | ✅ |
| **Cost** | Free | Pay-per | Pay-per | Free (open) |
| **Setup** | Easy | Instant | Easy | Complex |
| **Alerts** | Alertmanager | SNS | Built-in | Built-in |
| **Ecosystem** | Grafana | CloudWatch Dash | Dashboard | Kibana |
| **Python support** | ✅ | ✅ | ✅ | ✅ |
| **Score** | 9/10 | 7/10 | 8/10 | 7/10 |

### Recomendación
**Prometheus + Grafana** (for self-hosted/cost-effective)

```python
# main.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
request_count = Counter('yukyu_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('yukyu_request_duration_seconds', 'Request duration')
db_queries = Gauge('yukyu_db_queries_total', 'DB queries')

# Expose /metrics
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")

# Scrape config (prometheus.yml)
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'yukyu'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Decisión: ✅ ACEPTADA
**Implementar Sprint 3, Week 9**

---

## ADR-009: Testing Strategy - Unit vs Integration vs E2E

**Status:** ✅ ACCEPTED
**Date:** 2026-01-17

### Contexto
Actual: 61/62 pytest tests + 26 Jest tests

### Decisión
Target test pyramid:

```
        /\
       /  \        E2E (10%)
      /────\       ~6 tests
     /      \
    /   /\   \
   /   /  \   \    Integration (20%)
  /   /────\   \   ~12 tests
 /   /      \   \
/   /   /\   \   \
   /   /  \   \   Unit (70%)
  /   /────\   \
 /   /      \   \
/___/________\___\
```

### Targets
- **Unit:** 70% (functions, services, models)
- **Integration:** 20% (routes, database)
- **E2E:** 10% (full workflows, UI)

### Coverage Target
- **Backend:** 85%+ (code coverage)
- **Frontend:** 60%+ (Jest + Playwright)
- **Critical paths:** 100% (fiscal_year.py, compliance)

### Decisión: ✅ ACEPTADA
**Mantener + mejorar en Sprint 3**

---

## MATRIZ DE PRIORIZACIÓN

| ADR | Título | Prioridad | Esfuerzo | Impacto | Timeline |
|-----|--------|-----------|----------|---------|----------|
| 001 | Fix ID Schema | 🔴 CRÍTICO | 3d | 9/10 | W1-2 |
| 002 | Repository Pattern | 🔴 CRÍTICO | 4d | 8/10 | W1-2 |
| 004 | Alembic Migrations | 🟠 ALTO | 2d | 7/10 | W3 |
| 005 | Agentes → CLI | 🟠 ALTO | 2d | 6/10 | W4 |
| 003 | Frontend Consolidation | 🟠 ALTO | 10d | 8/10 | W5-8 |
| 009 | Testing Strategy | 🟠 ALTO | 5d | 7/10 | W9-11 |
| 007 | Hybrid Caching | 🟡 MEDIO | 2d | 5/10 | W9 |
| 008 | Prometheus Monitoring | 🟡 MEDIO | 2d | 6/10 | W9 |
| 006 | SQLAlchemy ORM | 📋 DEFERRED | 20d | 7/10 | W16+ |

---

## RECOMENDACIONES POR ROL

### Backend Engineer
- Priorizar ADR-001 (ID Schema)
- Implementar ADR-002 (Repository)
- Ejecutar ADR-004 (Migrations)
- Monitoreo ADR-008

### Frontend Engineer
- Ejecutar ADR-003 (Frontend consolidation)
- Juntar con backend para integración

### DevOps Engineer
- Setup ADR-008 (Prometheus)
- CI/CD improvements
- Deployment strategy

### QA Engineer
- ADR-009 (Testing strategy)
- E2E test suite
- Security testing

---

## APROBACIÓN

- [ ] CTO/Tech Lead
- [ ] Backend Team Lead
- [ ] Frontend Team Lead
- [ ] DevOps Team Lead
- [ ] Product Owner

**Siguiente reunión:** Semana 1, Sprint Planning
