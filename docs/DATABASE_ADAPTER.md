# Database Adapter - Abstraction Layer

## Overview

The `services/database_adapter.py` module provides a unified interface to switch between two database implementations without changing application code:

1. **Raw SQL** (`database.py`) - Production default, mature, optimized
2. **SQLAlchemy ORM** (`database_orm.py`) - Phase 2 migration, type-safe, more maintainable

## Architecture

```
Application Code
       ↓
Database Adapter (database_adapter.py)
       ↓ USE_ORM flag
       ├─→ ORM Implementation (database_orm.py) [if USE_ORM=true]
       └─→ Raw SQL Implementation (database.py) [if USE_ORM=false]
       ↓
Database (SQLite or PostgreSQL)
```

## Feature Flag: USE_ORM

Control which implementation is used via environment variable:

```bash
# Production (default)
export USE_ORM=false      # Use database.py (raw SQL)

# Development/Testing
export USE_ORM=true       # Use database_orm.py (ORM)
```

In `.env.example`:
```env
USE_ORM=false
```

## Why Use the Adapter?

### 1. Gradual Migration
Migrate from raw SQL to ORM incrementally without changing application code:
- Phase 1: Deploy adapter with `USE_ORM=false` (no behavior change)
- Phase 2: Enable ORM gradually in dev environments
- Phase 3: Switch to ORM in production when ready

### 2. Backward Compatibility
All functions maintain identical signatures and return types:
```python
# Code stays exactly the same regardless of implementation
employees = get_employees(year=2025)  # Works with both

# Both return: List[Dict] with same fields
# - id, name, balance, usage_rate, etc.
```

### 3. Easy Testing & Debugging
Switch implementations on-the-fly:
```python
# In tests, you can force a specific implementation
os.environ['USE_ORM'] = 'true'   # Test with ORM
# vs
os.environ['USE_ORM'] = 'false'  # Test with SQL
```

### 4. Comprehensive Logging
Track which implementation is used:
```
[DEBUG] Database Adapter initialized with USE_ORM=false
[DEBUG] [SQL] get_employees(year=2025) called
[DEBUG] [SQL] get_employees(year=2025) completed successfully
```

## Available Functions

### Employee Management

```python
# Read
get_employees(year=None, active_only=False) → List[Dict]
get_employee(employee_num, year) → Optional[Dict]
get_available_years() → List[int]
get_employees_enhanced(year=None, active_only=False) → List[Dict]

# Write
save_employee(employee_data) → None
save_employees(employees_data) → None

# History
get_employee_yukyu_history(employee_num, current_year=None) → List[Dict]
get_employee_total_balance(employee_num, year) → float
```

### Leave Requests

```python
# Read
get_leave_requests(status=None, employee_num=None, year=None) → List[Dict]
get_leave_request(request_id) → Optional[Dict]

# Write
approve_leave_request(request_id, approved_by) → bool
reject_leave_request(request_id, approved_by) → bool
```

### Employee Types

```python
# Dispatch Employees (派遣社員)
get_genzai(status=None, year=None, active_in_year=False) → List[Dict]
save_genzai(genzai_data) → None

# Contract Employees (請負社員)
get_ukeoi(status=None, year=None, active_in_year=False) → List[Dict]
save_ukeoi(ukeoi_data) → None

# Office Staff
get_staff(status=None, year=None, active_in_year=False) → List[Dict]
save_staff(staff_data) → None
```

### Usage Tracking

```python
# Detailed usage dates
get_yukyu_usage_details(employee_num=None, year=None, month=None) → List[Dict]
save_yukyu_usage_details(usage_details_list) → None

# Analytics
get_monthly_usage_summary(year) → Dict[int, Dict]
get_employee_usage_summary(employee_num, year) → Optional[Dict]
```

### Audit & Notifications

```python
# Audit logging
get_audit_log(entity_type=None, entity_id=None, limit=100) → List[Dict]

# Notifications
get_notifications(user_id) → List[Dict]
get_read_notification_ids(user_id) → set
```

### Status

```python
# Check current implementation
get_implementation_status() → Dict
```

## Usage Examples

### Basic Employee Query

```python
from services.database_adapter import get_employees

# Works with both implementations automatically
employees = get_employees(year=2025)

for emp in employees:
    print(f"{emp['name']}: {emp['balance']} days remaining")
```

### Batch Save from Excel

```python
from services.database_adapter import save_employees

# Typically called after Excel parsing
employees_data = [
    {
        "id": "001_2025",
        "employee_num": "001",
        "name": "田中太郎",
        "granted": 20.0,
        "used": 5.0,
        "balance": 15.0,
        "year": 2025,
    },
    # ... more employees
]

save_employees(employees_data)
```

### Leave Request Workflow

```python
from services.database_adapter import (
    get_leave_requests,
    approve_leave_request,
    reject_leave_request,
)

# Get pending requests
pending = get_leave_requests(status="PENDING", year=2025)

for request in pending:
    try:
        # Approve with automatic LIFO deduction
        approve_leave_request(
            request_id=request['id'],
            approved_by="admin_user"
        )
        print(f"✓ Approved: {request['employee_name']}")
    except ValueError as e:
        # Reject if not enough balance
        reject_leave_request(
            request_id=request['id'],
            approved_by="admin_user"
        )
        print(f"✗ Rejected: {e}")
```

### Check Implementation Status

```python
from services.database_adapter import get_implementation_status

status = get_implementation_status()

print(f"Implementation: {status['implementation']}")
print(f"Database: {status['database_type']}")
# Output:
# Implementation: Raw SQL (database.py)
# Database: sqlite
```

## Logging Configuration

The adapter logs all operations for debugging:

```python
# In .env
LOG_LEVEL=DEBUG    # Shows which implementation is used

# Output:
# [DEBUG] Database Adapter initialized with USE_ORM=false
# [DEBUG] [SQL] get_employees(year=2025) called
# [DEBUG] [SQL] get_employees(year=2025) completed successfully
```

For production, use:
```bash
LOG_LEVEL=INFO     # Only errors and important info
```

## Error Handling

The adapter provides consistent error handling:

```python
from services.database_adapter import get_employee

try:
    emp = get_employee("999", 2025)
    if not emp:
        print("Employee not found")
except ValueError as e:
    print(f"Invalid parameters: {e}")
except Exception as e:
    print(f"Database error: {e}")
    # Logs automatically include full traceback
```

## Performance Considerations

### Raw SQL (database.py)
- ✓ Mature, optimized queries
- ✓ Fine-grained control
- ✓ Direct parameter binding
- ✗ More boilerplate code

### ORM (database_orm.py)
- ✓ Type-safe
- ✓ Automatic relationship handling
- ✓ Easier to maintain
- ✗ Slightly higher overhead (trade-off for maintainability)

## Migration Guide

### Step 1: Deploy with USE_ORM=false (No Change)
```bash
# .env
USE_ORM=false

# Application code doesn't change
# adapter routes to database.py
```

### Step 2: Test with ORM in Development
```bash
# .env (dev only)
USE_ORM=true

# adapter routes to database_orm.py
# Run same tests, both implementations should pass
```

### Step 3: Gradual Production Rollout
```bash
# Test ORM thoroughly before production
# Stage 1: 10% of traffic (if using load balancer)
# Stage 2: 50% of traffic
# Stage 3: 100% of traffic
```

### Step 4: Remove Raw SQL (Post-Migration)
Once ORM is stable in production:
```python
# Remove database.py after Phase 2 is complete
# Remove adapter fallback logic
# Use database_orm.py directly
```

## Testing

### Unit Tests
```python
import os
from services.database_adapter import get_employees

def test_get_employees_with_sql():
    os.environ['USE_ORM'] = 'false'
    employees = get_employees(year=2025)
    assert len(employees) >= 0

def test_get_employees_with_orm():
    os.environ['USE_ORM'] = 'true'
    employees = get_employees(year=2025)
    assert len(employees) >= 0
    # Both tests should return identical results
```

### Integration Tests
```python
# Test workflow with both implementations
def test_leave_request_workflow(use_orm):
    os.environ['USE_ORM'] = str(use_orm).lower()

    # Workflow should work identically
    requests = get_leave_requests(status="PENDING")
    for req in requests:
        approve_leave_request(req['id'], "admin")
        # Balance should be deducted correctly
```

## Troubleshooting

### ORM Not Available
```
[WARNING] database_orm not available: ModuleNotFoundError
[ERROR] USE_ORM=true but database_orm module not found
[INFO] Falling back to raw SQL
```

**Solution:** Ensure `database_orm.py` exists and dependencies are installed

### Different Results Between Implementations
```python
# Debug mode to see which implementation is used
os.environ['LOG_LEVEL'] = 'DEBUG'

# Check returned fields are identical
result_sql = get_employees(year=2025)
result_orm = get_employees(year=2025)

assert len(result_sql) == len(result_orm)
assert result_sql[0].keys() == result_orm[0].keys()
```

## Future Enhancements

### Phase 2 (Current)
- [ ] Complete ORM implementations for all CRUD operations
- [ ] Add ORM-specific optimizations (lazy loading, eager loading)
- [ ] Performance benchmarking

### Phase 3 (Post-Migration)
- [ ] Remove raw SQL implementation
- [ ] Make ORM the default
- [ ] Advanced features (relationship caching, query optimization)

## Performance Monitoring

Add to your monitoring dashboard:

```python
from services.database_adapter import get_implementation_status

status = get_implementation_status()
metrics = {
    'implementation': status['implementation'],
    'database_type': status['database_type'],
    'orm_available': status['orm_available'],
}
```

## Related Files

- `services/database_adapter.py` - Main adapter implementation
- `database.py` - Raw SQL implementation
- `database_orm.py` - SQLAlchemy ORM implementation
- `examples/database_adapter_usage.py` - Usage examples
- `.env.example` - Configuration template

## Questions?

See also:
- [main.py endpoints](../main.py) - API layer using adapter
- [routes/v1/](../routes/v1/) - API routes
- [services/fiscal_year.py](../services/fiscal_year.py) - Business logic using adapter
