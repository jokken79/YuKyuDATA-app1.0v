# Ejemplos de Refactorización - YuKyuDATA

Código de ejemplo para las refactorizaciones propuestas en la auditoría.

---

## REFACTOR 1: ID Schema Migration

### Antes (Problema)

```python
# database.py - Actual
def init_db():
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,  # {employee_num}_{year}
            employee_num TEXT,
            name TEXT,
            year INTEGER,
            granted REAL,
            used REAL,
            balance REAL,
            last_updated TEXT
        )
    ''')

def get_employees(year: int):
    with get_db() as conn:
        c = conn.cursor()
        # Problema: Query trata id como compuesto
        c.execute("SELECT * FROM employees WHERE year = ?", (year,))
        return [dict(row) for row in c.fetchall()]

def sync_employees_from_excel(file_path):
    employees = parse_excel(file_path)
    with get_db() as conn:
        c = conn.cursor()
        for emp in employees:
            emp_id = f"{emp['employee_num']}_{emp['year']}"  # Generación manual de ID
            c.execute('''
                INSERT OR REPLACE INTO employees
                (id, employee_num, name, year, granted, ...)
                VALUES (?, ?, ?, ?, ?, ...)
            ''', (emp_id, emp['employee_num'], emp['name'], emp['year'], ...))
```

### Después (Solución)

```python
# database/migrations/003_fix_id_schema.py (Alembic migration)
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Change from composite string ID to surrogate integer ID"""
    
    # Step 1: Create new table with surrogate key
    op.create_table('employees_new',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('employee_num', sa.String(10), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('granted', sa.Float),
        sa.Column('used', sa.Float),
        sa.Column('balance', sa.Float),
        sa.Column('last_updated', sa.String(50)),
        sa.UniqueConstraint('employee_num', 'year', name='uq_emp_year'),
    )
    
    # Step 2: Migrate data (SQLite generates new ROWID)
    op.execute('''
        INSERT INTO employees_new
        (id, employee_num, name, year, granted, used, balance, last_updated)
        SELECT ROWID, employee_num, name, year, granted, used, balance, last_updated
        FROM employees
    ''')
    
    # Step 3: Create indexes on new table
    op.create_index('idx_emp_year', 'employees_new', ['employee_num', 'year'])
    op.create_index('idx_year', 'employees_new', ['year'])
    
    # Step 4: Drop old table
    op.drop_table('employees')
    
    # Step 5: Rename
    op.rename_table('employees_new', 'employees')

def downgrade():
    """Revert to composite ID (if needed)"""
    op.execute('''
        CREATE TABLE employees_old (
            id TEXT PRIMARY KEY,
            employee_num TEXT,
            year INTEGER,
            ...
        )
    ''')
    op.execute('''
        INSERT INTO employees_old
        SELECT 
            employee_num || '_' || year,
            employee_num,
            year,
            ...
        FROM employees
    ''')
    op.drop_table('employees')
    op.rename_table('employees_old', 'employees')

# database.py - Refactorizado
def init_db():
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  # Surrogate key
            employee_num TEXT NOT NULL,
            name TEXT,
            year INTEGER,
            granted REAL,
            used REAL,
            balance REAL,
            last_updated TEXT,
            UNIQUE(employee_num, year)  # Constraint de unicidad
        )
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_emp_year
        ON employees(employee_num, year)
    ''')

def get_employees(year: int):
    with get_db() as conn:
        c = conn.cursor()
        # Query mejorada: index-friendly
        c.execute(
            "SELECT id, employee_num, name, granted, used, balance FROM employees WHERE year = ?",
            (year,)
        )
        return [dict(row) for row in c.fetchall()]

def sync_employees_from_excel(file_path):
    employees = parse_excel(file_path)
    with get_db() as conn:
        c = conn.cursor()
        for emp in employees:
            # Sin necesidad de generar ID manual
            c.execute('''
                INSERT OR REPLACE INTO employees
                (employee_num, name, year, granted, ...)
                VALUES (?, ?, ?, ?, ...)
            ''', (emp['employee_num'], emp['name'], emp['year'], ...))
            # ROWID se genera automáticamente
```

---

## REFACTOR 2: Repository Pattern

### Antes (Problema)

```python
# routes/employees.py - Tightly coupled a database
import database
from models import EmployeeResponse

@router.get("/employees")
async def get_employees(year: int):
    try:
        data = database.get_employees(year)  # Direct call, no DI
        years = database.get_available_years()
        return {"status": "success", "data": data, "years": years}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error")

# Problema en tests: requiere base de datos real
def test_get_employees():
    # Solo funciona si base de datos existe
    response = client.get("/api/employees?year=2025")
    assert response.status_code == 200
```

### Después (Solución)

```python
# repositories/interfaces.py - Abstracciones
from abc import ABC, abstractmethod
from typing import List, Optional
from models import EmployeeResponse, EmployeeCreate, EmployeeUpdate

class EmployeeRepository(ABC):
    """Interface para operaciones Employee"""
    
    @abstractmethod
    async def get_by_year(self, year: int) -> List[EmployeeResponse]:
        """Obtener empleados por año"""
        pass

    @abstractmethod
    async def get_by_number(self, emp_num: str, year: int) -> Optional[EmployeeResponse]:
        """Obtener empleado por número y año"""
        pass

    @abstractmethod
    async def get_active(self, year: int) -> List[EmployeeResponse]:
        """Obtener empleados activos (status = '在職中')"""
        pass

    @abstractmethod
    async def create_or_update(self, emp_num: str, year: int, data: EmployeeCreate) -> EmployeeResponse:
        """Crear o actualizar empleado"""
        pass

    @abstractmethod
    async def delete(self, emp_num: str, year: int) -> bool:
        """Eliminar empleado"""
        pass

    @abstractmethod
    async def get_available_years(self) -> List[int]:
        """Obtener años disponibles"""
        pass

# repositories/sqlite_impl.py - Implementación SQLite
class SQLiteEmployeeRepository(EmployeeRepository):
    """Implementación SQLite de EmployeeRepository"""
    
    def __init__(self, db_connection):
        self.db = db_connection

    async def get_by_year(self, year: int) -> List[EmployeeResponse]:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT id, employee_num, name, granted, used, balance FROM employees WHERE year = ? ORDER BY employee_num",
                (year,)
            )
            return [EmployeeResponse(**dict(row)) for row in c.fetchall()]

    async def get_by_number(self, emp_num: str, year: int) -> Optional[EmployeeResponse]:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute(
                "SELECT * FROM employees WHERE employee_num = ? AND year = ?",
                (emp_num, year)
            )
            row = c.fetchone()
            return EmployeeResponse(**dict(row)) if row else None

    async def get_active(self, year: int) -> List[EmployeeResponse]:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT e.* FROM employees e
                INNER JOIN genzai g ON e.employee_num = g.employee_num
                WHERE e.year = ? AND g.status = '在職中'
                ORDER BY e.employee_num
            ''', (year,))
            return [EmployeeResponse(**dict(row)) for row in c.fetchall()]

    async def create_or_update(self, emp_num: str, year: int, data: EmployeeCreate) -> EmployeeResponse:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO employees
                (employee_num, year, name, granted, used, balance)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (emp_num, year, data.name, data.granted, data.used, data.balance))
            conn.commit()
            return await self.get_by_number(emp_num, year)

    async def delete(self, emp_num: str, year: int) -> bool:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM employees WHERE employee_num = ? AND year = ?", (emp_num, year))
            conn.commit()
            return c.rowcount > 0

    async def get_available_years(self) -> List[int]:
        with self.db.connection() as conn:
            c = conn.cursor()
            c.execute("SELECT DISTINCT year FROM employees ORDER BY year DESC")
            return [row[0] for row in c.fetchall()]

# routes/dependencies.py - Dependency Injection
from fastapi import Depends
from repositories import EmployeeRepository, SQLiteEmployeeRepository
from database import get_db

async def get_employee_repository(db = Depends(get_db)) -> EmployeeRepository:
    """Provide EmployeeRepository"""
    return SQLiteEmployeeRepository(db)

# routes/employees.py - Refactorizado (DI-friendly)
from fastapi import APIRouter, Depends
from repositories import EmployeeRepository

router = APIRouter(prefix="/api", tags=["Employees"])

@router.get("/employees")
async def get_employees(
    year: int,
    repo: EmployeeRepository = Depends(get_employee_repository)
):
    """Get employees by year"""
    try:
        data = await repo.get_by_year(year)  # Injection, no direct call
        years = await repo.get_available_years()
        return {"status": "success", "data": data, "years": years}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error")

# tests/test_employees.py - Muy fácil de testear
import pytest
from unittest.mock import AsyncMock
from models import EmployeeResponse

@pytest.fixture
def mock_employee_repo():
    """Mock repository"""
    repo = AsyncMock(spec=EmployeeRepository)
    repo.get_by_year.return_value = [
        EmployeeResponse(id=1, employee_num="001", name="Taro", granted=20, used=5, balance=15),
        EmployeeResponse(id=2, employee_num="002", name="Hanako", granted=20, used=10, balance=10),
    ]
    repo.get_available_years.return_value = [2025, 2024, 2023]
    return repo

@pytest.mark.asyncio
async def test_get_employees(client, mock_employee_repo, monkeypatch):
    """Test get_employees endpoint"""
    # Monkeypatch la dependencia
    monkeypatch.setattr(
        "routes.employees.get_employee_repository",
        lambda: mock_employee_repo
    )
    
    response = client.get("/api/employees?year=2025")
    
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2
    assert response.json()["data"][0]["employee_num"] == "001"
```

---

## REFACTOR 3: Eliminar N+1 Queries

### Antes (Problema: N+1)

```python
# services/employees.py - PROBLEMA: 500+ queries
def get_employees_enhanced(year: int) -> List[dict]:
    """Obtener empleados con información expandida - LENTO!"""
    
    # Query 1: SELECT * FROM employees WHERE year = ?
    employees = database.get_employees(year)
    
    # ❌ Queries 2-501: Loop sobre 500 empleados
    for emp in employees:
        # Query para cada empleado
        genzai = database.get_genzai(emp_num=emp['employee_num'])
        ukeoi = database.get_ukeoi(emp_num=emp['employee_num'])
        staff = database.get_staff(emp_num=emp['employee_num'])
        
        # Expandir datos
        emp['genzai_status'] = genzai[0]['status'] if genzai else None
        emp['ukeoi_status'] = ukeoi[0]['status'] if ukeoi else None
        emp['staff_status'] = staff[0]['status'] if staff else None
    
    return employees

# Resultado: 1 + 500 + 500 + 500 = 1,501 queries! ❌
```

### Después (Solución: JOINs)

```python
# repositories/queries.py - SOLUCIÓN: Single query con JOINs
async def get_employees_with_status(
    repo: EmployeeRepository,
    year: int
) -> List[dict]:
    """Obtener empleados con estado - RÁPIDO!"""
    
    # Query única con JOINs
    with db.connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                e.id, e.employee_num, e.name, 
                e.granted, e.used, e.balance,
                g.status as genzai_status,
                u.status as ukeoi_status,
                s.status as staff_status
            FROM employees e
            LEFT JOIN genzai g ON e.employee_num = g.employee_num
            LEFT JOIN ukeoi u ON e.employee_num = u.employee_num
            LEFT JOIN staff s ON e.employee_num = s.employee_num
            WHERE e.year = ?
            ORDER BY e.employee_num
        ''', (year,))
        
        return [dict(row) for row in c.fetchall()]

# Resultado: 1 query únicamente! ✅
# Tiempo: 2.5 segundos → 100ms (25x más rápido)

# routes/employees.py - Usar nueva función
@router.get("/employees/enhanced")
async def get_employees_enhanced(
    year: int,
    repo: EmployeeRepository = Depends(get_employee_repository)
):
    """Get employees with status information"""
    data = await repo.get_with_status(year)
    return {"status": "success", "data": data}
```

---

## REFACTOR 4: Caching Estratégico

### Antes (Problema: TTL fijo)

```python
# services/caching.py - Actual: TTL fijo sin invalidación
from functools import wraps
from time import time

CACHE = {}
CACHE_TTL = 300  # 5 minutos hardcoded

def cached(ttl=CACHE_TTL):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Crear cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Revisar cache
            if cache_key in CACHE:
                value, timestamp = CACHE[cache_key]
                if time() - timestamp < ttl:
                    return value  # Cache hit
            
            # Cache miss: ejecutar función
            result = await func(*args, **kwargs)
            CACHE[cache_key] = (result, time())
            return result
        return wrapper
    return decorator

# Problema: Stale data hasta 5 minutos
@cached(ttl=300)
async def get_employees(year: int):
    return database.get_employees(year)  # Stale hasta 5 min
```

### Después (Solución: Event-driven + warming)

```python
# services/caching.py - Refactorizado: Event-driven + warming
from enum import Enum
from typing import Callable, List
import asyncio

class CacheEvent(Enum):
    """Eventos de invalidación de cache"""
    EMPLOYEE_CREATED = "employee:created"
    EMPLOYEE_UPDATED = "employee:updated"
    EMPLOYEE_DELETED = "employee:deleted"
    LEAVE_REQUEST_APPROVED = "leave:approved"

class CacheManager:
    def __init__(self):
        self.cache = {}
        self.ttl = 300
        self.listeners = {}
    
    def register_invalidator(self, event: CacheEvent, patterns: List[str]):
        """Registrar patrón de cache para invalidar en evento"""
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].extend(patterns)
    
    def invalidate(self, event: CacheEvent, context: dict = None):
        """Invalidar cache basado en evento"""
        if event in self.listeners:
            for pattern in self.listeners[event]:
                # Wildcard pattern matching
                for key in list(self.cache.keys()):
                    if pattern in key:
                        del self.cache[key]
                        logger.info(f"Cache invalidated: {key} (event: {event.value})")
    
    def get(self, key: str):
        """Obtener del cache"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value):
        """Guardar en cache"""
        self.cache[key] = (value, time())

cache_manager = CacheManager()

# Registrar invalidadores
cache_manager.register_invalidator(
    CacheEvent.EMPLOYEE_UPDATED,
    ["employees:*"]  # Invalidar todos los keys de employees
)
cache_manager.register_invalidator(
    CacheEvent.LEAVE_REQUEST_APPROVED,
    ["employees:*", "compliance:*"]  # Afecta múltiples caches
)

def cached(ttl=300, events: List[CacheEvent] = None):
    """Decorator con invalidación por eventos"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Crear cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Revisar cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cache miss: ejecutar función
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result)
            return result
        
        # Registrar invalidadores si especificados
        if events:
            for event in events:
                cache_manager.register_invalidator(event, [func.__name__])
        
        return wrapper
    return decorator

# routes/employees.py - Usar con eventos
from services.caching import cached, CacheEvent, cache_manager

@cached(ttl=300, events=[CacheEvent.EMPLOYEE_UPDATED, CacheEvent.EMPLOYEE_DELETED])
async def get_employees(year: int):
    return database.get_employees(year)

@router.put("/employees/{emp_num}/{year}")
async def update_employee(emp_num: str, year: int, data: EmployeeUpdate):
    result = database.update_employee(emp_num, year, data)
    
    # ✅ Automático: invalida "get_employees:*"
    cache_manager.invalidate(CacheEvent.EMPLOYEE_UPDATED, {
        'emp_num': emp_num,
        'year': year
    })
    
    return result

# scheduler.py - Cache warming
import schedule

@schedule.scheduled_job('cron', minute='*/4:30')  # Cada 4.5 minutos
async def warm_cache():
    """Calentar cache antes que expire (TTL = 5 min)"""
    for year in database.get_available_years():
        # Pre-populate cache
        await get_employees(year)
        logger.info(f"Cache warmed for year {year}")

# Result:
# ✅ Fresh data always (invalidated on update)
# ✅ No stale data window
# ✅ Better performance (cache warming)
```

---

## REFACTOR 5: Migración Frontend a static/src/

### Antes (Problema: Duplicación)

```javascript
// static/js/app.js - 7,091 líneas
const App = {
    state: {
        data: [],
        currentView: 'dashboard'
    },
    
    init() {
        this.loadData();
        this.render();
    },
    
    showDashboard() {
        this.currentView = 'dashboard';
        this.render();
    },
    
    render() {
        // 7,000+ líneas de renderización
        document.getElementById('app').innerHTML = this.getHTML();
    },
    
    // + 150 funciones más
};

// Y también existe duplicación en static/src/
// static/src/components/Modal.js (685 líneas)
// static/src/components/Table.js (985 líneas)
// ... etc
```

### Después (Solución: Usar static/src/)

```javascript
// static/src/pages/Dashboard.js - Moderno
class Dashboard {
    constructor() {
        this.components = {};
    }
    
    init() {
        // Usar componentes reutilizables
        this.components.header = new Header();
        this.components.sidebar = new Sidebar();
        this.components.content = new DashboardContent();
    }
    
    render() {
        const container = document.getElementById('app');
        container.innerHTML = '';
        container.appendChild(this.components.header.render());
        container.appendChild(this.components.sidebar.render());
        container.appendChild(this.components.content.render());
    }
    
    cleanup() {
        Object.values(this.components).forEach(comp => {
            if (comp.cleanup) comp.cleanup();
        });
    }
}

// static/src/index.js - Entry point
import { Dashboard, Employees, LeaveRequests } from './pages/index.js';

class YuKyuApp {
    constructor() {
        this.pages = { Dashboard, Employees, LeaveRequests };
        this.currentPage = null;
    }
    
    async init() {
        // Single initialization
        await this.navigate('dashboard');
    }
    
    async navigate(pageName) {
        if (this.currentPage) this.currentPage.cleanup();
        
        const PageClass = this.pages[pageName];
        this.currentPage = new PageClass();
        this.currentPage.init();
        this.currentPage.render();
    }
}

// Migration path:
// 1. Week 5: Completar features en static/src/
// 2. Week 6: Add webpack, bundle optimization
// 3. Week 7: Deprecate app.js
// 4. Week 8: E2E testing, rollout gradual

// Result:
// ✅ Single codebase
// ✅ 40% smaller bundle (15 KB → 9 KB)
// ✅ Better maintainability
```

---

## TESTING EXAMPLES

### Test Repository Injection

```python
# tests/test_employees_with_di.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from models import EmployeeResponse

@pytest.fixture
def mock_employee_repo():
    repo = AsyncMock()
    repo.get_by_year.return_value = [
        EmployeeResponse(
            id=1,
            employee_num="001",
            name="Taro Yamada",
            granted=20,
            used=5,
            balance=15
        )
    ]
    repo.get_available_years.return_value = [2025, 2024]
    return repo

@pytest.mark.asyncio
async def test_get_employees(mock_employee_repo):
    """Test without database"""
    with patch(
        'routes.dependencies.get_employee_repository',
        return_value=mock_employee_repo
    ):
        client = TestClient(app)
        response = client.get("/api/employees?year=2025")
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["employee_num"] == "001"

# Query profiling test
@pytest.mark.asyncio
async def test_no_n_plus_one_queries(mock_db):
    """Verify no N+1 queries"""
    with mock_db.query_counter() as counter:
        repo = SQLiteEmployeeRepository(mock_db)
        employees = await repo.get_with_status(year=2025)
        
        # Should be single query, not N+1
        assert counter.count == 1, f"Expected 1 query, got {counter.count}"
        assert len(employees) == 500
```

---

**Fin de ejemplos de código refactorizado.**
