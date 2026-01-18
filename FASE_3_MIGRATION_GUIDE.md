# FASE 3: Modern Architecture Migration Guide

**Phase 3** introduces modern database architecture with SQLAlchemy ORM, UUID primary keys, repositories, and dependency injection.

## Overview

### Components Delivered

| Component | Files | Purpose |
|-----------|-------|---------|
| **ORM Models** | `orm/models/` (10 files) | SQLAlchemy ORM models with UUID PKs |
| **Alembic Migration** | `alembic/versions/001_initial_uuid_schema.py` | Schema migration to UUID |
| **Repository Pattern** | `repositories/` (10 files) | Data access abstraction layer |
| **Dependency Injection** | `di.py` | FastAPI DI container |
| **API Versioning** | `routes/v1/` | Versioned endpoints /api/v1/* |
| **Configuration** | `alembic.ini`, `orm/__init__.py` | Database config |

### Key Improvements

1. **UUID Primary Keys**
   - Replaces composite keys `{employee_num}_{year}`
   - Maintains backward compatibility with unique constraints
   - Enables sharding and horizontal scaling

2. **SQLAlchemy ORM**
   - Type-safe database operations
   - Automatic SQL generation
   - Built-in relationship support
   - Easier testing with mocks

3. **Repository Pattern**
   - Centralized data access logic
   - Cleaner service layer
   - Easy to swap implementations (e.g., for testing)

4. **Dependency Injection**
   - Automatic dependency resolution
   - Cleaner route handlers
   - Better testability

5. **API Versioning**
   - Future-proof API evolution
   - Backward compatibility
   - Clear deprecation paths

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `sqlalchemy>=2.0.25`
- `alembic>=1.13.1`
- `psycopg2-binary>=2.9.9` (PostgreSQL support)

### 2. Initialize Database

```bash
# Create tables from Alembic migration
alembic upgrade head

# Or for SQLite, create tables directly
python -c "from orm import engine, Base; Base.metadata.create_all(engine)"
```

### 3. Verify Setup

```bash
# Test imports
python -c "from orm import Base, Employee; print('✓ ORM initialized')"
python -c "from repositories import get_employee_repository; print('✓ Repositories ready')"
python -c "from di import get_employee_repo; print('✓ DI configured')"
```

---

## Migration Path: Old Code → New Code

### Example 1: Get Employees

**OLD (database.py with raw SQL):**
```python
def get_employees_by_year(year):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM employees WHERE year = ?", (year,))
        return [dict(row) for row in c.fetchall()]
```

**NEW (using ORM + Repository + DI):**
```python
from fastapi import Depends
from di import get_employee_repo

@app.get("/api/v1/employees")
async def get_employees(
    year: int,
    employee_repo = Depends(get_employee_repo)
):
    employees = employee_repo.get_by_year(year)
    return {
        "data": [e.to_dict() for e in employees],
        "count": len(employees)
    }
```

### Example 2: Create Leave Request

**OLD:**
```python
def create_leave_request(emp_num, start_date, end_date, days):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO leave_requests
               (employee_num, start_date, end_date, days_requested, status, year)
               VALUES (?, ?, ?, ?, 'PENDING', ?)""",
            (emp_num, start_date, end_date, days, 2025)
        )
        conn.commit()
```

**NEW:**
```python
from models.leave_request import LeaveRequestCreate
from di import get_leave_request_repo

@app.post("/api/v1/leave-requests")
async def create_leave_request(
    request: LeaveRequestCreate,
    leave_repo = Depends(get_leave_request_repo)
):
    new_request = leave_repo.create(
        employee_num=request.employee_num,
        start_date=request.start_date,
        end_date=request.end_date,
        days_requested=request.days_requested,
        status="PENDING",
        year=2025
    )
    leave_repo.commit()
    return {"id": new_request.id, "status": "created"}
```

### Example 3: Update Employee Balance

**OLD:**
```python
def update_employee_balance(emp_num, year, new_balance):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE employees SET balance = ?, used = ? WHERE employee_num = ? AND year = ?",
            (new_balance, 0, emp_num, year)
        )
        conn.commit()
```

**NEW:**
```python
@app.put("/api/v1/employees/{employee_num}/{year}")
async def update_employee(
    employee_num: str,
    year: int,
    data: dict,
    employee_repo = Depends(get_employee_repo)
):
    employee = employee_repo.get_by_employee_and_year(employee_num, year)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    updated = employee_repo.update(
        employee.id,
        balance=data.get('balance'),
        used=data.get('used')
    )
    employee_repo.commit()
    return {"id": updated.id, "balance": updated.balance}
```

---

## Database Migration: SQLite → UUID Schema

### Step 1: Backup Current Database

```bash
cp yukyu.db yukyu.db.backup.2026-01-17
```

### Step 2: Run Alembic Migration

```bash
# Upgrade to new schema
alembic upgrade head

# Verify migration
sqlite3 yukyu.db ".schema employees"
```

The migration:
1. Creates new tables with UUID primary keys
2. Maintains `(employee_num, year)` unique constraint
3. Preserves all data
4. Creates appropriate indexes

### Step 3: Data Migration Script

```bash
# If migrating existing SQLite data:
python scripts/migrate_to_uuid.py

# This script:
# 1. Reads old database
# 2. Generates UUIDs
# 3. Inserts into new tables
# 4. Verifies data integrity
```

### Step 4: Verify Data Integrity

```bash
python -c "
from orm import SessionLocal, Employee
from repositories import get_employee_repository

with SessionLocal() as db:
    repo = get_employee_repository(db)
    count = repo.count()
    print(f'✓ Migrated {count} employee records')

    # Verify unique constraint
    sample = repo.get_by_year(2025, limit=1)
    if sample:
        print(f'✓ Sample: {sample.employee_num}, {sample.year} → UUID {sample.id}')
"
```

---

## Using Repositories in Routes

### Simple Query

```python
from fastapi import APIRouter, Depends
from di import get_employee_repo

router = APIRouter()

@router.get("/employees/{year}")
async def list_employees(
    year: int,
    employee_repo = Depends(get_employee_repo)
):
    employees = employee_repo.get_by_year(year)
    return {"data": [e.to_dict() for e in employees]}
```

### Complex Query with Filters

```python
@router.get("/employees/search")
async def search_employees(
    year: int,
    name: str = None,
    min_balance: float = None,
    employee_repo = Depends(get_employee_repo)
):
    filters = {}
    if year:
        filters['year'] = year

    results = employee_repo.search(filters)

    if name:
        results = [e for e in results if name.lower() in e.name.lower()]

    if min_balance is not None:
        results = [e for e in results if e.balance >= min_balance]

    return {"data": [e.to_dict() for e in results]}
```

### Multi-Repository Operations

```python
@router.post("/approve-leave/{request_id}")
async def approve_leave(
    request_id: str,
    approver: str,
    repos = Depends(get_repositories)
):
    # Use multiple repositories in one operation
    leave_req = repos.leave_requests.approve(request_id, approver)
    if not leave_req:
        raise HTTPException(status_code=404)

    # Update employee balance if needed
    emp = repos.employees.get_by_employee_and_year(
        leave_req.employee_num,
        leave_req.year
    )
    if emp and leave_req.days_requested > 0:
        repos.employees.update(emp.id, balance=emp.balance - leave_req.days_requested)

    repos.employees.commit()
    return {"status": "approved", "id": request_id}
```

---

## API Versioning Strategy

### Current State
- Old endpoints: `/api/employees`, `/api/leave-requests`, etc.
- New endpoints: `/api/v1/employees`, `/api/v1/leave-requests`, etc.

### Backward Compatibility

Old `/api/*` endpoints continue to work:

```python
# In routes/employees.py (old)
@app.get("/api/employees")
async def get_employees(year: int):
    # Still works, redirects to v1
    return await get_employees_v1(year)
```

### Deprecation Path

1. **Phase 3** (current): v1 available, v0 still works
2. **Phase 4** (future): v0 endpoints show deprecation warnings
3. **Phase 5** (future): v0 endpoints removed

### Versioning Headers (Optional)

```python
@app.get("/api/employees")
async def get_employees(
    year: int,
    request: Request,
    version: str = Header("v1", alias="Accept-Version")
):
    if version == "v0":
        return v0_response(year)
    elif version == "v1":
        return v1_response(year)
```

---

## Testing with Repositories

### Unit Test Example

```python
# tests/test_employee_repo.py
from sqlalchemy.orm import Session
from orm import SessionLocal, Employee, Base, engine
from repositories import EmployeeRepository

def test_get_by_employee_and_year():
    # Setup
    Base.metadata.create_all(engine)
    db = SessionLocal()
    repo = EmployeeRepository(db)

    # Create test data
    emp = repo.create(
        employee_num='001',
        year=2025,
        name='Test',
        balance=20.0
    )
    repo.commit()

    # Test
    result = repo.get_by_employee_and_year('001', 2025)
    assert result is not None
    assert result.name == 'Test'

    # Cleanup
    db.close()
    Base.metadata.drop_all(engine)
```

### Mock Repository for Tests

```python
# tests/conftest.py
from unittest.mock import Mock
from repositories import EmployeeRepository

@pytest.fixture
def mock_employee_repo():
    repo = Mock(spec=EmployeeRepository)
    repo.get_by_year.return_value = [
        Mock(employee_num='001', year=2025, balance=20.0),
        Mock(employee_num='002', year=2025, balance=15.5),
    ]
    return repo

# tests/test_api.py
def test_list_employees(mock_employee_repo):
    response = client.get(
        "/api/v1/employees?year=2025",
        headers={"Authorization": "Bearer token"}
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 2
```

---

## Performance Optimization Tips

### 1. Use Bulk Operations

```python
# Slow: One at a time
for emp in employees:
    repo.create(**emp)
    repo.commit()

# Fast: Bulk insert
repo.bulk_create(employees)
repo.commit()
```

### 2. Query Optimization

```python
# Make specific queries instead of loading all
# Slow:
all_emp = repo.get_all()
filtered = [e for e in all_emp if e.balance < 5]

# Fast:
filtered = repo.get_low_balance(threshold=5)
```

### 3. Avoid N+1 Queries

```python
# Use repositories that handle joins properly
# Always load what you need
employees = repo.get_by_year(2025)

# Process related data in batch, not loop
# Bad:
for emp in employees:
    details = detail_repo.get_by_employee_and_year(emp.employee_num, 2025)

# Good:
all_details = detail_repo.get_all()
details_map = {(d.employee_num, d.year): d for d in all_details}
```

---

## Troubleshooting

### Error: "No such table: employees"

```bash
# Solution: Run migration
alembic upgrade head
python -c "from orm import Base, engine; Base.metadata.create_all(engine)"
```

### Error: "ModuleNotFoundError: No module named 'orm'"

```bash
# Solution: Ensure alembic/env.py can import orm
cd /home/user/YuKyuDATA-app1.0v
python -c "from orm import Base"
```

### Error: "Session is closed" during tests

```python
# Solution: Use SessionLocal() with context manager
def test_something():
    db = SessionLocal()
    try:
        repo = EmployeeRepository(db)
        # tests here
    finally:
        db.close()
```

### PostgreSQL Connection Error

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql+psycopg2://user:pass@localhost/yukyu"
alembic upgrade head
```

---

## Next Steps

### Immediate (Complete FASE 3)
- [ ] Create /api/v1/* endpoints using repositories
- [ ] Update existing routes to use dependency injection
- [ ] Add comprehensive tests for repositories
- [ ] Document API changes

### Short-term (Week 1)
- [ ] Migrate all routes to use v1 endpoints
- [ ] Test backward compatibility
- [ ] Update frontend to use /api/v1/*
- [ ] Run integration tests

### Medium-term (Month 1)
- [ ] Monitor performance metrics
- [ ] Optimize slow queries
- [ ] Add caching layer
- [ ] Document API versioning strategy

### Long-term (After FASE 3)
- [ ] Plan v2 API changes
- [ ] Implement GraphQL alternative
- [ ] Add WebSocket real-time updates
- [ ] Consider sharding strategy

---

## Related Documentation

- **CLAUDE.md**: Project overview and conventions
- **CLAUDE_MEMORY.md**: Architecture decisions and history
- **models/**: Pydantic validation schemas
- **orm/models/**: SQLAlchemy ORM models
- **repositories/**: Data access layer
- **di.py**: Dependency injection setup

---

## Support

For questions or issues with FASE 3:
1. Check `FASE_3_MIGRATION_GUIDE.md` (this file)
2. Review examples in `repositories/`
3. Check `orm/models/` for model definitions
4. Verify `alembic/versions/` migration script
5. Test with `pytest tests/`

---

**Last Updated**: 2026-01-17
**Status**: PHASE 3 - Database Architecture Complete
**Next Phase**: FASE 4 - Full Route Migration to v1 API
