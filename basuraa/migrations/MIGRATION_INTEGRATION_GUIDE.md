# UUID Migration Integration Guide

**Document:** FASE 4 Phase 1 Backward Compatibility & Integration
**Date:** 2026-01-17
**Version:** 1.0

---

## Overview

This guide explains how to use the UUID migration backward compatibility layer and integrate it into the application codebase.

### Three Migration Phases

1. **Phase 1 (Current):** UUID migration completed, backward compatibility available
2. **Phase 2 (Next 4 weeks):** Gradual code migration to UUID-based queries
3. **Phase 3 (Final):** Complete removal of composite key patterns

---

## Part 1: Backward Compatibility Layer

### Location
```
scripts/uuid-compatibility-layer.py
```

### Core Functions

#### 1. Get Employee UUID (Composite Key → UUID)
```python
from scripts.uuid_compatibility import get_employee_uuid

# Given employee_num and year, get UUID
uuid = get_employee_uuid("001", 2025)
# Returns: "a1b2c3d4-e5f6-...-..." or None if not found
```

**Use Case:** When you have employee_num and year but need the UUID.

#### 2. Get Employee by Composite Key (Legacy Interface)
```python
from scripts.uuid_compatibility import get_employee_by_composite_key

# Get full employee record using composite key
emp = get_employee_by_composite_key("001", 2025)
# Returns: {"id": "uuid...", "employee_num": "001", "year": 2025, ...}
```

**Use Case:** Backward compatibility during migration - works the same as before.

#### 3. Get Employee by UUID (Modern Interface)
```python
from scripts.uuid_compatibility import get_employee_by_uuid

# Get full employee record using UUID
emp = get_employee_by_uuid("a1b2c3d4-e5f6-...-...")
# Returns: {"id": "uuid...", "employee_num": "001", ...}
```

**Use Case:** Modern way - preferred for all new code.

#### 4. Get All Employee ID Mappings
```python
from scripts.uuid_compatibility import get_all_employee_ids

# Get mapping of composite keys to UUIDs
mapping = get_all_employee_ids()
# Returns: {"001_2025": "uuid...", "002_2025": "uuid...", ...}
```

**Use Case:** Bulk operations, cache population, audit trails.

### Cache Functions

```python
from scripts.uuid_compatibility import (
    populate_uuid_cache,
    clear_uuid_cache,
    get_cache_stats
)

# Pre-populate cache for better performance
count = populate_uuid_cache()
print(f"Cached {count} employees")

# Get cache statistics
stats = get_cache_stats()
print(f"Cache: {stats['size']}/{stats['max_size']}")  # e.g., 10/1000

# Clear cache (if needed)
clear_uuid_cache()
```

---

## Part 2: Integration Patterns

### Pattern 1: Direct Replacement (No Code Changes)

**Before:**
```python
from database import get_db

with get_db() as conn:
    c = conn.cursor()
    c.execute(
        "SELECT * FROM employees WHERE employee_num = ? AND year = ?",
        ("001", 2025)
    )
    employee = c.fetchone()
```

**After (Method A - With Compatibility Layer):**
```python
from scripts.uuid_compatibility import get_employee_by_composite_key

employee = get_employee_by_composite_key("001", 2025)
# Same result, cleaner code
```

**After (Method B - Modern UUID):**
```python
from scripts.uuid_compatibility import get_employee_uuid, get_employee_by_uuid

employee_id = get_employee_uuid("001", 2025)
if employee_id:
    employee = get_employee_by_uuid(employee_id)
```

### Pattern 2: Gradual Migration (Composite Key → UUID)

**Step 1: Use compatibility layer**
```python
# routes/employees.py
from scripts.uuid_compatibility import get_employee_by_composite_key

@app.get("/api/employees/{emp_num}/{year}")
def get_employee(emp_num: str, year: int):
    employee = get_employee_by_composite_key(emp_num, year)
    return employee
```

**Step 2: Update endpoint to accept UUID**
```python
# Later: Allow both composite key and UUID
@app.get("/api/employees/{emp_id}")  # Now emp_id can be UUID
def get_employee(emp_id: str):
    # Try as UUID first (new way)
    employee = get_employee_by_uuid(emp_id)

    # Fall back to composite key (legacy way)
    if not employee and '_' in emp_id:
        emp_num, year = emp_id.split('_')
        employee = get_employee_by_composite_key(emp_num, int(year))

    return employee
```

**Step 3: Deprecate composite key**
```python
# Finally: Remove composite key support entirely
@app.get("/api/employees/{emp_id}")
def get_employee(emp_id: str):
    employee = get_employee_by_uuid(emp_id)
    if not employee:
        raise NotFound("Employee not found")
    return employee
```

### Pattern 3: Batch Operations

```python
from scripts.uuid_compatibility import get_all_employee_ids, get_employee_by_uuid

# Get all employees efficiently
mapping = get_all_employee_ids()

for composite_key, employee_id in mapping.items():
    employee = get_employee_by_uuid(employee_id)
    # Process each employee
    process_employee(employee)
```

### Pattern 4: Cache Optimization

```python
from scripts.uuid_compatibility import populate_uuid_cache, get_cache_stats

# At application startup
def on_startup():
    # Pre-populate cache
    count = populate_uuid_cache()
    stats = get_cache_stats()
    logger.info(f"UUID cache: {stats['size']}/{stats['max_size']} populated")

# Monitor cache hit rate
def on_request():
    stats = get_cache_stats()
    if stats['fill_percent'] > 90:
        logger.warning("UUID cache near capacity")
```

---

## Part 3: Database Query Migration

### SQL Query Migration

**Before (Composite Key):**
```sql
SELECT * FROM employees WHERE employee_num = ? AND year = ?
```

**After (UUID):**
```sql
SELECT * FROM employees WHERE id = ?
```

**Transition (Both):**
```sql
-- During migration period, support both
SELECT * FROM employees
WHERE id = ? OR (employee_num = ? AND year = ?)
```

### ORM Query Migration

**Before (Raw SQL):**
```python
from database import get_db

with get_db() as conn:
    c = conn.cursor()
    c.execute(
        "SELECT * FROM employees WHERE employee_num = ? AND year = ?",
        ("001", 2025)
    )
    rows = c.fetchall()
```

**After (ORM):**
```python
from orm.models import Employee
from sqlalchemy import select

# Query by UUID (preferred)
stmt = select(Employee).where(Employee.id == employee_id)
employees = session.execute(stmt).scalars()

# Or with composite key (transitional)
stmt = select(Employee).where(
    (Employee.employee_num == "001") & (Employee.year == 2025)
)
employees = session.execute(stmt).scalars()
```

---

## Part 4: API Endpoint Migration

### Example: Employee Endpoints

#### GET /api/employees (List)

**Before:**
```python
@app.get("/api/employees")
def list_employees(year: int = 2025):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM employees WHERE year = ?",
            (year,)
        )
        employees = [dict(row) for row in c.fetchall()]
    return employees
```

**After (Immediate - Minimal Changes):**
```python
from scripts.uuid_compatibility import populate_uuid_cache

@app.on_event("startup")
async def startup():
    # Pre-warm cache
    populate_uuid_cache()

@app.get("/api/employees")
def list_employees(year: int = 2025):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM employees WHERE year = ?",
            (year,)
        )
        employees = [dict(row) for row in c.fetchall()]
    return employees
    # No code change needed - UUID already in id column
```

**After (Complete Migration):**
```python
from orm.models import Employee
from sqlalchemy import select

@app.get("/api/employees")
def list_employees(year: int = 2025):
    stmt = select(Employee).where(Employee.year == year)
    employees = [emp.to_dict() for emp in session.execute(stmt).scalars()]
    return employees
```

#### GET /api/employees/{emp_id} (Detail)

**Transition Pattern (Supports Both Composite Key and UUID):**
```python
from scripts.uuid_compatibility import (
    get_employee_by_uuid,
    get_employee_by_composite_key
)

@app.get("/api/employees/{emp_id}")
def get_employee_detail(emp_id: str):
    """
    Get employee by UUID or composite key.

    Examples:
    - GET /api/employees/a1b2c3d4-e5f6-...  (UUID)
    - GET /api/employees/001_2025            (Composite key, legacy)
    """

    # Try UUID first
    emp = get_employee_by_uuid(emp_id)

    # Fall back to composite key format
    if not emp and '_' in emp_id:
        parts = emp_id.split('_')
        if len(parts) == 2:
            emp_num, year_str = parts
            try:
                emp = get_employee_by_composite_key(emp_num, int(year_str))
            except ValueError:
                pass

    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    return emp
```

---

## Part 5: Testing & Validation

### Unit Tests

```python
import pytest
from scripts.uuid_compatibility import (
    get_employee_uuid,
    get_employee_by_composite_key,
    get_employee_by_uuid
)

class TestUUIDCompatibility:
    def test_get_employee_uuid(self):
        """Test getting UUID by composite key."""
        uuid = get_employee_uuid("001", 2025)
        assert uuid is not None
        assert len(uuid) == 36  # UUID format

    def test_get_employee_by_composite_key(self):
        """Test legacy interface."""
        emp = get_employee_by_composite_key("001", 2025)
        assert emp is not None
        assert emp['employee_num'] == "001"

    def test_get_employee_by_uuid(self):
        """Test modern interface."""
        uuid = get_employee_uuid("001", 2025)
        emp = get_employee_by_uuid(uuid)
        assert emp is not None
        assert emp['id'] == uuid

    def test_composite_and_uuid_return_same_employee(self):
        """Test both methods return same data."""
        emp1 = get_employee_by_composite_key("001", 2025)
        emp2 = get_employee_by_uuid(emp1['id'])
        assert emp1 == emp2
```

### Integration Tests

```python
def test_employee_endpoint_with_composite_key():
    """Test endpoint works with composite key."""
    response = client.get("/api/employees/001_2025")
    assert response.status_code == 200
    assert response.json()['employee_num'] == "001"

def test_employee_endpoint_with_uuid():
    """Test endpoint works with UUID."""
    # Get UUID first
    emp = get_employee_by_composite_key("001", 2025)
    uuid = emp['id']

    # Now query by UUID
    response = client.get(f"/api/employees/{uuid}")
    assert response.status_code == 200
    assert response.json()['id'] == uuid
```

---

## Part 6: Monitoring & Logging

### Enable Migration Logging

```python
from scripts.uuid_compatibility import log_legacy_call, get_migration_report

# In routes that still use composite keys
def legacy_endpoint():
    log_legacy_call(
        "legacy_endpoint",
        context="Still using composite key lookup"
    )
    # ... rest of function

# Generate migration report
def admin_migration_status():
    report = get_migration_report()
    return {"status": report}
```

### Log File Example

```
Legacy Code Path Migration Report
==================================================

Function: get_employee_by_composite_key
  Calls: 15
  - routes/employees.py:45
  - services/reports.py:102
  - background_jobs.py:89
  ... and 12 more

Function: legacy_endpoint
  Calls: 8
  - routes/admin.py:23
  ... and 7 more
```

---

## Part 7: Rollout Plan

### Week 1-2: Preparation
- [x] UUID migration completed
- [ ] Team review of compatibility layer
- [ ] Create test data with mixed ID types
- [ ] Set up monitoring for legacy calls

### Week 3-4: Phase 1 Rollout
- [ ] Deploy with compatibility layer active
- [ ] Monitor application logs
- [ ] Document any issues
- [ ] No code changes to application

### Week 5-6: Phase 2 Rollout
- [ ] Refactor critical endpoints (employees, leave_requests)
- [ ] Update tests to use UUID
- [ ] Update API documentation
- [ ] Deprecate composite key endpoints

### Week 7-8: Phase 3 Rollout
- [ ] Remove composite key support from new code
- [ ] Migrate all remaining queries
- [ ] Deprecate compatibility layer
- [ ] Clean up legacy code

### Week 9+: Phase 4
- [ ] Complete ORM integration
- [ ] Remove all raw SQL where possible
- [ ] PostgreSQL support with native UUID type
- [ ] Soft delete implementation

---

## Part 8: Troubleshooting

### Issue: UUID Lookup Fails

**Symptom:** `get_employee_by_uuid()` returns None

**Solution:**
```python
# Verify UUID exists in database
uuid = get_employee_uuid("001", 2025)
if uuid:
    print(f"Employee found with UUID: {uuid}")
else:
    print("Employee not found")
    # Check if employee exists at all
    emp = get_employee_by_composite_key("001", 2025)
    if emp:
        print(f"Employee found with composite key, UUID: {emp['id']}")
```

### Issue: Cache Getting Full

**Symptom:** Cache fill percent > 90%

**Solution:**
```python
from scripts.uuid_compatibility import clear_uuid_cache, populate_uuid_cache

# Clear and repopulate
clear_uuid_cache()
count = populate_uuid_cache()
print(f"Repopulated {count} entries")

# Or increase cache size in uuid-compatibility-layer.py:
# CACHE_SIZE = 1000  # Change this to 2000 or higher
```

### Issue: Performance Degradation

**Symptom:** Queries slower than before

**Solution:**
```python
# Enable caching
populate_uuid_cache()

# Use get_employee_by_uuid instead of composite key
# UUID queries are faster once cached

# Check cache stats
stats = get_cache_stats()
print(f"Cache efficiency: {stats['fill_percent']:.1f}%")
```

---

## Part 9: Code Examples

### Complete Example: Migration of Employees Route

**Before Migration:**
```python
# routes/employees.py - OLD VERSION
from database import get_db

@app.get("/api/employees/{emp_num}/{year}")
def get_employee(emp_num: str, year: int):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM employees WHERE employee_num = ? AND year = ?",
            (emp_num, year)
        )
        employee = c.fetchone()

    if not employee:
        raise HTTPException(status_code=404)

    return dict(employee)
```

**During Migration (Phase 1-2):**
```python
# routes/employees.py - TRANSITION VERSION
from scripts.uuid_compatibility import (
    get_employee_by_composite_key,
    get_employee_by_uuid
)

@app.get("/api/employees/{emp_id}")
def get_employee(emp_id: str):
    """
    Get employee by UUID or composite key.

    Supports:
    - /api/employees/a1b2c3d4-e5f6-...  (UUID)
    - /api/employees/001_2025            (Composite key)
    """

    # Try UUID first (new way)
    emp = get_employee_by_uuid(emp_id)

    # Fall back to composite key (legacy way)
    if not emp and '_' in emp_id:
        parts = emp_id.split('_')
        if len(parts) == 2:
            emp_num, year_str = parts
            try:
                emp = get_employee_by_composite_key(emp_num, int(year_str))
            except ValueError:
                pass

    if not emp:
        raise HTTPException(status_code=404)

    return emp
```

**After Migration (Phase 3+):**
```python
# routes/employees.py - FINAL VERSION
from orm.models import Employee
from sqlalchemy import select
from database import SessionLocal

@app.get("/api/employees/{emp_id}")
def get_employee(emp_id: str):
    """
    Get employee by UUID (only).

    Example:
    - /api/employees/a1b2c3d4-e5f6-...
    """

    session = SessionLocal()
    try:
        stmt = select(Employee).where(Employee.id == emp_id)
        emp = session.execute(stmt).scalar_one_or_none()

        if not emp:
            raise HTTPException(status_code=404)

        return emp.to_dict()
    finally:
        session.close()
```

---

## Summary

### Key Takeaways

1. **UUID migration is complete** - All employees have UUIDs
2. **Backward compatibility available** - Old code continues to work
3. **Gradual migration possible** - Refactor at your own pace
4. **Cache optimization available** - Improve performance with caching
5. **Clear migration path** - 3 phases to complete modernization

### Quick Start

```python
# Start using UUIDs immediately
from scripts.uuid_compatibility import get_employee_by_uuid

emp = get_employee_by_uuid("a1b2c3d4-e5f6-...-...")

# Or keep using composite keys temporarily
from scripts.uuid_compatibility import get_employee_by_composite_key

emp = get_employee_by_composite_key("001", 2025)
```

### Next Steps

1. Deploy application (with updated database)
2. Update critical endpoints to accept UUIDs
3. Monitor for performance issues
4. Plan refactoring schedule
5. Migrate code in phases

---

**For questions or issues, refer to:**
- `MIGRATION_REPORT.md` - Technical migration details
- `MIGRATION_CHECKLIST.md` - Pre/post migration checklist
- `scripts/uuid-compatibility-layer.py` - Implementation details
