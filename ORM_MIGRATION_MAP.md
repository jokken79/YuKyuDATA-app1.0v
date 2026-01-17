# ORM Migration Map - FASE 4 Phase 2

Complete mapping of all SQL queries in `database.py` for migration to SQLAlchemy ORM.

**Status:** FASE 4 Phase 2 - In Progress
**Total Queries to Migrate:** ~81 (excluding schema operations)
**ORM Models Available:** 10 entities in `/orm/models/`

---

## Query Summary

| Type | Count | Status | Priority |
|------|-------|--------|----------|
| **SELECT (Read)** | 41 | Not Started | High |
| **INSERT (Create)** | 15 | Not Started | High |
| **UPDATE (Update)** | 15 | Not Started | High |
| **DELETE (Delete)** | 10 | Not Started | Medium |
| **CREATE (Schema)** | 94 | Skip (ORM handles) | N/A |
| **TOTAL CRUD** | **81** | **In Progress** | - |

---

## ORM Models Available

| Entity | Status | Lines | Fields |
|--------|--------|-------|--------|
| `Employee` | ✅ Ready | 75 | id, employee_num, year, name, haken, granted, used, balance, expired, usage_rate, created_at, updated_at |
| `LeaveRequest` | ✅ Ready | 90 | id, employee_num, employee_name, start_date, end_date, days_requested, hours_requested, leave_type, reason, status, year, hourly_wage, approver, approved_at, created_at |
| `YukyuUsageDetail` | ✅ Ready | 70 | id, employee_num, use_date, days_used, created_at, updated_at |
| `GenzaiEmployee` | ✅ Ready | 95 | (dispatch employee fields) |
| `UkeoiEmployee` | ✅ Ready | 85 | (contractor employee fields) |
| `StaffEmployee` | ✅ Ready | 75 | (office staff fields) |
| `User` | ✅ Ready | 80 | id, username, email, password_hash, role, created_at, updated_at |
| `Notification` | ✅ Ready | 85 | id, user_id, title, message, type, priority, is_read, created_at |
| `AuditLog` | ✅ Ready | 95 | id, entity_type, entity_id, action, user_id, timestamp |
| `NotificationRead` | ✅ Ready | 60 | id, notification_id, user_id, read_at |

---

## PHASE 1: READ OPERATIONS (SELECT) - 41 Queries

Priority: **HIGH** - Least risky, good starting point

### Subtask 1.1: Basic Employee Reads (10 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 1 | `get_employees(year)` | `SELECT * FROM employees WHERE year = ?` | Low | `session.query(Employee).filter_by(year=year).all()` |
| 2 | `get_employee(emp_num, year)` | `SELECT * FROM employees WHERE employee_num = ? AND year = ?` | Low | `session.query(Employee).filter_by(employee_num=emp_num, year=year).first()` |
| 3 | `get_available_years()` | `SELECT DISTINCT YEAR FROM EMPLOYEES ORDER BY YEAR DESC` | Low | `session.query(Employee.year).distinct().order_by(Employee.year.desc()).all()` |
| 4 | `get_employees_enhanced()` | `SELECT * FROM employees WHERE year = ? ORDER BY employee_num` | Low | `session.query(Employee).filter_by(year=year).order_by(Employee.employee_num).all()` |
| 5 | `get_employee_total_balance(emp_num, year)` | `SELECT COALESCE(SUM(balance), 0) FROM employees WHERE employee_num = ? AND year >= ?` | Medium | Aggregate - See Subtask 3.1 |
| 6 | `get_genzai(status, year)` | `SELECT * FROM genzai WHERE status = ? AND year = ?` | Low | `session.query(GenzaiEmployee).filter_by(status=status, year=year).all()` |
| 7 | `get_ukeoi(status, year)` | `SELECT * FROM ukeoi WHERE status = ? AND year = ?` | Low | `session.query(UkeoiEmployee).filter_by(status=status, year=year).all()` |
| 8 | `get_staff(status, year)` | `SELECT * FROM staff WHERE status = ? AND year = ?` | Low | `session.query(StaffEmployee).filter_by(status=status, year=year).all()` |
| 9 | `get_employee_hourly_wage(emp_num)` | `SELECT hourly_wage FROM genzai WHERE employee_num = ?` | Low | Needs refactoring - data is in different tables |
| 10 | `get_stats_by_factory(year)` | Complex aggregation by dispatch location | High | See Subtask 3.2 |

### Subtask 1.2: Leave Request Reads (8 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 11 | `get_leave_requests(status, emp_num, year)` | `SELECT * FROM leave_requests WHERE status = ? AND employee_num = ? AND year = ?` | Low | `session.query(LeaveRequest).filter(LeaveRequest.status==status, LeaveRequest.employee_num==emp_num, LeaveRequest.year==year).all()` |
| 12 | `get_leave_request(request_id)` | `SELECT * FROM leave_requests WHERE id = ?` | Low | `session.query(LeaveRequest).filter_by(id=request_id).first()` |
| 13 | `get_employee_yukyu_history(emp_num, year)` | `SELECT * FROM leave_requests WHERE employee_num = ? AND year = ? ORDER BY created_at DESC` | Low | `session.query(LeaveRequest).filter_by(employee_num=emp_num, year=year).order_by(LeaveRequest.created_at.desc()).all()` |
| 14 | `get_leave_requests_by_period(start_date, end_date)` | `SELECT * FROM leave_requests WHERE start_date >= ? AND end_date <= ?` | Low | Date range filter |
| 15 | `get_approved_leave_count(emp_num, year)` | `SELECT COUNT(*) FROM leave_requests WHERE employee_num = ? AND year = ? AND status = 'APPROVED'` | Medium | Aggregate query |
| 16 | `get_pending_approvals()` | `SELECT * FROM leave_requests WHERE status = 'PENDING' ORDER BY created_at` | Low | `session.query(LeaveRequest).filter_by(status='PENDING').order_by(LeaveRequest.created_at).all()` |
| 17 | Complex leave workflow query | Multi-join with employees table | High | See Subtask 2.5 (Joins) |
| 18 | Get leave request with employee details | JOIN employees and leave_requests | Medium | See Subtask 2.5 |

### Subtask 1.3: Yukyu Usage Detail Reads (6 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 19 | `get_yukyu_usage_details(emp_num, year)` | `SELECT * FROM yukyu_usage_details WHERE employee_num = ? AND year = ?` | Low | `session.query(YukyuUsageDetail).filter_by(employee_num=emp_num, year=year).all()` |
| 20 | `get_monthly_usage_summary(year)` | Group by month, aggregate days_used | Medium | Aggregate query - See Subtask 3.1 |
| 21 | `get_usage_detail(detail_id)` | `SELECT * FROM yukyu_usage_details WHERE id = ?` | Low | `session.query(YukyuUsageDetail).filter_by(id=detail_id).first()` |
| 22 | Get usage by employee and month | Complex aggregation | High | See Subtask 3.2 |
| 23 | Get usage trend | Time-series aggregation | High | See Subtask 3.2 |
| 24 | Get usage by department | Join and aggregate | High | See Subtask 3.2 |

### Subtask 1.4: Notification Reads (5 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 25 | `get_notifications(user_id)` | `SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC` | Low | `session.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()` |
| 26 | `get_notification(notification_id)` | `SELECT * FROM notifications WHERE id = ?` | Low | `session.query(Notification).filter_by(id=notification_id).first()` |
| 27 | `is_notification_read(notification_id, user_id)` | `SELECT * FROM notification_reads WHERE notification_id = ? AND user_id = ?` | Low | `session.query(NotificationRead).filter_by(notification_id=notification_id, user_id=user_id).first()` |
| 28 | `get_read_notification_ids(user_id)` | `SELECT notification_id FROM notification_reads WHERE user_id = ?` | Low | `session.query(NotificationRead.notification_id).filter_by(user_id=user_id).all()` |
| 29 | `get_unread_count(user_id)` | `SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0` | Medium | Aggregate - `func.count()` |

### Subtask 1.5: User & Auth Reads (4 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 30 | `get_user(user_id)` | `SELECT * FROM users WHERE id = ?` | Low | `session.query(User).filter_by(id=user_id).first()` |
| 31 | `get_user_by_username(username)` | `SELECT * FROM users WHERE username = ?` | Low | `session.query(User).filter_by(username=username).first()` |
| 32 | `get_user_by_email(email)` | `SELECT * FROM users WHERE email = ?` | Low | `session.query(User).filter_by(email=email).first()` |
| 33 | `get_all_users()` | `SELECT * FROM users` | Low | `session.query(User).all()` |
| 34 | `get_refresh_token_by_hash(hash)` | `SELECT * FROM refresh_tokens WHERE token_hash = ? AND revoked = 0` | Low | Filter with multiple conditions |
| 35 | `get_user_active_refresh_tokens(user_id)` | `SELECT * FROM refresh_tokens WHERE user_id = ? AND revoked = 0 AND expires_at > NOW()` | Low | Filter with time condition |

### Subtask 1.6: Audit Log Reads (4 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 36 | `get_audit_log(limit, offset)` | `SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ? OFFSET ?` | Low | Pagination pattern |
| 37 | `get_audit_log_by_user(user_id)` | `SELECT * FROM audit_log WHERE user_id = ? ORDER BY timestamp DESC` | Low | Filter + order by |
| 38 | `get_entity_history(entity_type, entity_id)` | `SELECT * FROM audit_log WHERE entity_type = ? AND entity_id = ? ORDER BY timestamp DESC` | Low | Filter + order by |
| 39 | `get_audit_stats(days)` | Complex aggregation on date range | High | See Subtask 3.2 |
| 40 | `get_bulk_update_history(operation_id)` | Complex join and aggregation | High | See Subtask 2.5 |
| 41 | `get_get_refresh_token_stats()` | Count and aggregate refresh token metrics | Medium | See Subtask 3.1 |

---

## PHASE 2: CREATE OPERATIONS (INSERT) - 15 Queries

Priority: **HIGH** - Enable new data creation

### Subtask 2.1: Employee Inserts (3 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 42 | `save_employees(list)` | `INSERT OR REPLACE INTO employees VALUES (...)` - Bulk | High | `session.bulk_insert_mappings(Employee, employee_list)` |
| 43 | `save_genzai(list)` | `INSERT OR REPLACE INTO genzai VALUES (...)` - Bulk | High | `session.bulk_insert_mappings(GenzaiEmployee, data)` |
| 44 | `save_ukeoi(list)` | `INSERT OR REPLACE INTO ukeoi VALUES (...)` - Bulk | High | `session.bulk_insert_mappings(UkeoiEmployee, data)` |
| 45 | `save_staff(list)` | `INSERT OR REPLACE INTO staff VALUES (...)` - Bulk | High | `session.bulk_insert_mappings(StaffEmployee, data)` |

### Subtask 2.2: Leave Request Inserts (2 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 46 | `create_leave_request(...)` | `INSERT INTO leave_requests VALUES (...)` | Low | `session.add(LeaveRequest(...))` |
| 47 | `add_single_yukyu_usage(...)` | `INSERT INTO yukyu_usage_details VALUES (...)` | Low | `session.add(YukyuUsageDetail(...))` |

### Subtask 2.3: Yukyu Detail Inserts (2 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 48 | `save_yukyu_usage_details(list)` | `INSERT INTO yukyu_usage_details VALUES (...)` - Bulk | Medium | `session.bulk_insert_mappings(YukyuUsageDetail, details)` |
| 49 | Bulk usage detail insert | Multiple row insert | Medium | Bulk insert |

### Subtask 2.4: Notification/User Inserts (4 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 50 | `create_notification(...)` | `INSERT INTO notifications VALUES (...)` | Low | `session.add(Notification(...))` |
| 51 | `mark_notification_read(...)` | `INSERT INTO notification_reads VALUES (...)` | Low | `session.add(NotificationRead(...))` |
| 52 | `store_refresh_token(...)` | `INSERT INTO refresh_tokens VALUES (...)` | Low | `session.add(RefreshToken(...))` |
| 53 | `create_user(...)` | `INSERT INTO users VALUES (...)` | Low | `session.add(User(...))` |

### Subtask 2.5: Audit Log Inserts (4 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 54 | `log_audit(...)` | `INSERT INTO audit_log VALUES (...)` | Low | `session.add(AuditLog(...))` |
| 55 | `bulk_update_employees_with_audit(...)` | Multi-insert with audit trail | High | Batch inserts + audit logging |
| 56 | Bulk insert audit from operation | Complex bulk with relations | High | Requires careful transaction handling |

---

## PHASE 3: UPDATE OPERATIONS (UPDATE) - 15 Queries

Priority: **HIGH** - Critical for data modifications

### Subtask 3.1: Employee Updates (6 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 57 | `update_employee(emp_num, year, **kwargs)` | `UPDATE employees SET balance = ?, used = ? WHERE employee_num = ? AND year = ?` | Low | Update specific fields |
| 58 | `approve_leave_request(request_id)` | `UPDATE leave_requests SET status = 'APPROVED' WHERE id = ?` + `UPDATE employees SET balance = balance - ? WHERE ...` | Medium | Two-step update |
| 59 | `reject_leave_request(request_id)` | `UPDATE leave_requests SET status = 'REJECTED' WHERE id = ?` | Low | Simple status update |
| 60 | `update_employee_balance(emp_num, year, new_balance)` | `UPDATE employees SET balance = ? WHERE employee_num = ? AND year = ?` | Low | Single field update |
| 61 | `recalculate_employee_used_days(emp_num, year)` | Calculate from details + `UPDATE employees SET used = ? WHERE ...` | Medium | Computed field update |
| 62 | `bulk_update_employees(emp_nums, year, updates)` | `UPDATE employees SET ... WHERE employee_num IN (...)` - Multiple rows | High | Batch update |

### Subtask 3.2: Leave Request Updates (4 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 63 | `revert_approved_request(request_id)` | `UPDATE leave_requests SET status = 'REVERTED' WHERE id = ?` + restore balance | Medium | Two-step update |
| 64 | `cancel_leave_request(request_id)` | `UPDATE leave_requests SET status = 'CANCELLED' WHERE id = ?` | Low | Status update |
| 65 | `mark_all_notifications_read(user_id, ids)` | `UPDATE notification_reads SET read_at = NOW() WHERE notification_id IN (...)` | Medium | Batch update |
| 66 | Update leave request dates | Modify start_date, end_date after creation | Low | Field updates |

### Subtask 3.3: Token & Auth Updates (3 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 67 | `revoke_refresh_token(token_hash)` | `UPDATE refresh_tokens SET revoked = 1, revoked_at = NOW() WHERE token_hash = ?` | Low | Flag update |
| 68 | `revoke_all_user_refresh_tokens(user_id)` | `UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?` | Low | Batch flag update |
| 69 | `update_user_password(user_id, new_hash)` | `UPDATE users SET password_hash = ? WHERE id = ?` | Low | Field update |

### Subtask 3.4: Complex Updates (2 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 70 | `apply_lifo_deduction(emp_num, days, year)` | Complex conditional update (most recent days first) | High | See Subtask 4.2 (Complex) |
| 71 | `process_year_end_carryover(from_year, to_year)` | Multi-table update with carry-over logic | High | See Subtask 4.2 (Complex) |

---

## PHASE 4: DELETE OPERATIONS (DELETE) - 10 Queries

Priority: **MEDIUM** - Less frequent, careful handling

### Subtask 4.1: Data Cleanup (10 queries)

| # | Function | SQL Pattern | Complexity | ORM Pattern |
|---|----------|-------------|-----------|-------------|
| 72 | `clear_database()` | `DELETE FROM employees` | Low | `session.query(Employee).delete()` |
| 73 | `clear_genzai()` | `DELETE FROM genzai` | Low | `session.query(GenzaiEmployee).delete()` |
| 74 | `clear_ukeoi()` | `DELETE FROM ukeoi` | Low | `session.query(UkeoiEmployee).delete()` |
| 75 | `clear_staff()` | `DELETE FROM staff` | Low | `session.query(StaffEmployee).delete()` |
| 76 | `clear_yukyu_usage_details()` | `DELETE FROM yukyu_usage_details` | Low | `session.query(YukyuUsageDetail).delete()` |
| 77 | `delete_yukyu_usage_detail(detail_id)` | `DELETE FROM yukyu_usage_details WHERE id = ?` | Low | `session.query(YukyuUsageDetail).filter_by(id=detail_id).delete()` |
| 78 | `delete_old_yukyu_records(cutoff_year)` | `DELETE FROM leave_requests WHERE year < ?` | Low | Filter and delete |
| 79 | `cleanup_expired_refresh_tokens()` | `DELETE FROM refresh_tokens WHERE expires_at < NOW()` | Low | Filter by date and delete |
| 80 | `cleanup_old_audit_logs(days_to_keep)` | `DELETE FROM audit_log WHERE timestamp < DATE_SUB(NOW(), INTERVAL ? DAY)` | Low | Date-based deletion |
| 81 | `revert_bulk_update(operation_id)` | Complex delete with rollback logic | High | See Subtask 4.2 (Complex) |

---

## PHASE 5: AGGREGATE OPERATIONS - 20+ Queries

Priority: **MEDIUM** - Data analysis queries

### Subtask 5.1: Count Aggregates (5 queries)

| # | Query | SQL Pattern | ORM Pattern |
|---|-------|-------------|-------------|
| A1 | Count employees by year | `SELECT COUNT(*) FROM employees WHERE year = ?` | `session.query(func.count(Employee.id)).filter_by(year=year).scalar()` |
| A2 | Count leave requests by status | `SELECT status, COUNT(*) FROM leave_requests GROUP BY status` | Group by with count |
| A3 | Count active employees | `SELECT COUNT(*) FROM genzai WHERE status = '在職中'` | Filter + count |
| A4 | Count pending approvals | `SELECT COUNT(*) FROM leave_requests WHERE status = 'PENDING'` | Filter + count |
| A5 | Unread notification count | `SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0` | Filter + count |

### Subtask 5.2: Sum Aggregates (5 queries)

| # | Query | SQL Pattern | ORM Pattern |
|---|-------|-------------|-------------|
| S1 | Total balance per employee | `SELECT SUM(balance) FROM employees WHERE employee_num = ? AND year >= ?` | `func.sum()` with filter |
| S2 | Total days used by year | `SELECT SUM(days_used) FROM yukyu_usage_details WHERE year = ?` | `func.sum()` with filter |
| S3 | Total granted per department | `SELECT haken, SUM(granted) FROM employees GROUP BY haken` | Group by + sum |
| S4 | Total approved days per employee | `SELECT SUM(days_requested) FROM leave_requests WHERE employee_num = ? AND status = 'APPROVED'` | Filter + sum |
| S5 | Total expired days | `SELECT SUM(expired) FROM employees WHERE year < YEAR(NOW())` | Time-based sum |

### Subtask 5.3: Avg/Min/Max Aggregates (5 queries)

| # | Query | SQL Pattern | ORM Pattern |
|---|-------|-------------|-------------|
| AM1 | Average usage rate | `SELECT AVG(usage_rate) FROM employees WHERE year = ?` | `func.avg()` |
| AM2 | Max balance | `SELECT MAX(balance) FROM employees WHERE year = ?` | `func.max()` |
| AM3 | Min balance | `SELECT MIN(balance) FROM employees WHERE year = ?` | `func.min()` |
| AM4 | Salary statistics | `SELECT MIN(hourly_wage), MAX(hourly_wage), AVG(hourly_wage) FROM genzai` | Multiple aggregates |
| AM5 | Leave days distribution | Complex percentile analysis | Custom aggregation |

### Subtask 5.4: Group By Operations (5+ queries)

| # | Query | SQL Pattern | Complexity | ORM Pattern |
|---|-------|-------------|-----------|-------------|
| G1 | Usage by month | `SELECT MONTH(use_date), SUM(days_used) FROM yukyu_usage_details GROUP BY MONTH(use_date)` | Medium | Group by with date function |
| G2 | Employees by status | `SELECT status, COUNT(*) FROM genzai GROUP BY status` | Low | Group by with count |
| G3 | Leave requests by approver | `SELECT approver, COUNT(*) FROM leave_requests GROUP BY approver` | Low | Group by with count |
| G4 | Usage by department | `SELECT haken, SUM(used), COUNT(*) FROM employees GROUP BY haken` | Medium | Group by + multiple aggregates |
| G5 | Compliance by division | Complex multi-table group | High | Join + group by |

---

## PHASE 6: COMPLEX & JOIN QUERIES - 15+ Queries

Priority: **HIGH** - Critical business logic

### Subtask 6.1: Join Operations (5 queries)

| # | Query | SQL Pattern | Complexity | ORM Pattern |
|---|-------|-------------|-----------|-------------|
| J1 | Leave requests with employee details | `SELECT lr.*, e.name, e.haken FROM leave_requests lr JOIN employees e ON lr.employee_num = e.employee_num` | Medium | `query(LeaveRequest).join(Employee, ...).all()` |
| J2 | Notifications with read status | `SELECT n.*, nr.read_at FROM notifications n LEFT JOIN notification_reads nr ON n.id = nr.notification_id WHERE nr.user_id = ?` | Medium | Left join pattern |
| J3 | Audit log with user details | `SELECT al.*, u.username FROM audit_log al JOIN users u ON al.user_id = u.id` | Low | Join with users |
| J4 | Leave request history with approver | `SELECT lr.*, u.username as approver_name FROM leave_requests lr LEFT JOIN users u ON lr.approver = u.id` | Medium | Left join |
| J5 | Usage details with employee summary | `SELECT yud.*, e.name, e.balance FROM yukyu_usage_details yud JOIN employees e ON yud.employee_num = e.employee_num` | Medium | Join + aggregate |

### Subtask 6.2: Multi-Table Queries (5 queries)

| # | Query | Function | Complexity | Current Implementation |
|---|-------|----------|-----------|------------------------|
| M1 | Compliance check with leave requests | Verify 5-day requirement with approved leaves | High | Multiple queries + Python logic |
| M2 | Year-end carry-over logic | Calculate expired + carried-over days | High | Complex conditional logic |
| M3 | LIFO deduction | Deduce from most recent leaves first | High | Subqueries + conditional update |
| M4 | Balance breakdown per year | Show granted, used, expired, balance per year | Medium | Multiple joins + aggregation |
| M5 | Department usage report | Summary across departments with year-over-year | High | Multi-table aggregation |

### Subtask 6.3: Subquery Operations (5 queries)

| # | Query | SQL Pattern | Complexity | Notes |
|---|-------|-------------|-----------|-------|
| SQ1 | Employees with no leave requests | `SELECT * FROM employees WHERE employee_num NOT IN (SELECT DISTINCT employee_num FROM leave_requests)` | Medium | Subquery in WHERE |
| SQ2 | Leave requests with max created_at | Get most recent request per employee | Medium | Window function or subquery |
| SQ3 | Employees exceeding balance limit | Find those > 40 days balance | Low | Simple filter |
| SQ4 | Top 10 most used vacation days | `SELECT employee_num, SUM(days_used) FROM leave_requests GROUP BY employee_num ORDER BY SUM(days_used) DESC LIMIT 10` | Low | Group by + order by |
| SQ5 | Expired days by year | Complex logic with date calculations | High | Custom aggregation |

---

## Migration Strategy

### Execution Order (Recommended)

1. **Phase 1: Read Operations** (8 hours)
   - Start with simple filters (low risk)
   - Validate ORM queries match raw SQL output
   - Test with various filters and conditions

2. **Phase 2: Create Operations** (3 hours)
   - Simple inserts first (low risk)
   - Bulk inserts with `bulk_insert_mappings()` (high risk, test thoroughly)
   - Validate auto-increment and generated IDs

3. **Phase 3: Update Operations** (3 hours)
   - Single-field updates (low risk)
   - Multi-field updates (medium risk)
   - Transaction handling for multi-step updates

4. **Phase 4: Delete Operations** (1 hour)
   - Soft deletes (if applicable)
   - Hard deletes (careful with referential integrity)

5. **Phase 5: Aggregate Operations** (2 hours)
   - Simple aggregates (COUNT, SUM)
   - Group by operations
   - Complex aggregations with conditions

6. **Phase 6: Complex Queries** (2 hours)
   - Join operations
   - Multi-table queries
   - Subquery equivalents

### Per-Query Checklist

For each query migrated:

- [ ] Extract original SQL from `database.py`
- [ ] Identify equivalent ORM operation
- [ ] Write ORM code in new function
- [ ] Compare output data types (dict, list, scalar)
- [ ] Write unit test with sample data
- [ ] Verify backward compatibility
- [ ] Test with both SQLite and PostgreSQL (if applicable)
- [ ] Document any behavior changes
- [ ] Commit with specific query migration message

### Key Patterns

#### Simple Filter (1 condition)
```python
# OLD
c.execute("SELECT * FROM employees WHERE year = ?", (year,))

# NEW
session.query(Employee).filter_by(year=year).all()
```

#### Multiple Filters
```python
# OLD
c.execute("SELECT * FROM employees WHERE employee_num = ? AND year = ?", (emp_num, year))

# NEW
session.query(Employee).filter_by(employee_num=emp_num, year=year).first()
```

#### Aggregate SUM
```python
from sqlalchemy import func

# OLD
c.execute("SELECT COALESCE(SUM(balance), 0) FROM employees WHERE year = ?", (year,))
result = c.fetchone()[0]

# NEW
total = session.query(func.sum(Employee.balance)).filter_by(year=year).scalar() or 0.0
```

#### Bulk Insert
```python
# OLD
for emp in emp_list:
    c.execute("INSERT INTO employees VALUES (...)", (emp['emp_num'], emp['year'], ...))
conn.commit()

# NEW
session.bulk_insert_mappings(Employee, emp_list)
session.commit()
```

#### Join Query
```python
from sqlalchemy.orm import joinedload

# OLD
c.execute("""SELECT lr.*, e.name FROM leave_requests lr
             JOIN employees e ON lr.employee_num = e.employee_num
             WHERE lr.year = ?""", (year,))

# NEW
results = session.query(LeaveRequest).join(
    Employee,
    (LeaveRequest.employee_num == Employee.employee_num) &
    (LeaveRequest.year == Employee.year)
).filter(LeaveRequest.year == year).all()
```

#### Group By with Aggregate
```python
from sqlalchemy import func

# OLD
c.execute("SELECT status, COUNT(*) as count FROM leave_requests GROUP BY status")

# NEW
results = session.query(
    LeaveRequest.status,
    func.count(LeaveRequest.id)
).group_by(LeaveRequest.status).all()
```

---

## Testing Strategy

### Unit Tests (1 test per query)

```python
# tests/orm/test_employee_crud.py
import pytest
from orm import Session
from orm.models import Employee

@pytest.fixture
def session():
    db = SessionLocal()
    yield db
    db.rollback()
    db.close()

def test_get_employees(session):
    # Setup
    emp1 = Employee(employee_num="001", year=2025, name="Taro", granted=10.0)
    emp2 = Employee(employee_num="002", year=2025, name="Hanako", granted=11.0)
    session.add_all([emp1, emp2])
    session.commit()

    # Execute (ORM query)
    results = session.query(Employee).filter_by(year=2025).all()

    # Verify
    assert len(results) == 2
    assert results[0].name == "Taro"
```

### Integration Tests

Verify functions still work with callers:

```python
# tests/integration/test_database_functions.py
def test_get_employees_function():
    from database import get_employees

    # Save test data
    save_employees([
        {'employee_num': '001', 'year': 2025, 'name': 'Taro', ...}
    ])

    # Query function
    result = get_employees(2025)

    # Verify
    assert len(result) == 1
    assert result[0]['name'] == 'Taro'
```

### Performance Tests

Ensure < 20% overhead:

```python
import timeit

# Time raw SQL
sql_time = timeit.timeit(
    'get_employees_raw_sql(2025)',
    globals=globals(),
    number=1000
)

# Time ORM
orm_time = timeit.timeit(
    'get_employees_orm(2025)',
    globals=globals(),
    number=1000
)

overhead_percent = ((orm_time - sql_time) / sql_time) * 100
assert overhead_percent < 20, f"ORM overhead too high: {overhead_percent}%"
```

---

## Known Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Data type consistency** | Always return same types (dict, list, scalar). Use `.to_dict()` on models if needed |
| **Bulk operations performance** | Use `bulk_insert_mappings()` not individual `add()` for large batches |
| **Composite keys** | ORM models use UUID pk, but maintain unique constraint on (emp_num, year) |
| **PostgreSQL/SQLite diffs** | Test both databases. Avoid database-specific SQL functions |
| **Legacy ID format** | Some code expects `{emp_num}_{year}` IDs. May need adapter functions |
| **Transaction handling** | SQLAlchemy auto-commits per session. Be careful with rollback logic |
| **Null handling** | ORM filters differently. Use `.is_(None)` for NULL, not `== None` |
| **Circular imports** | Keep models in separate files. Use TYPE_CHECKING for forward refs |

---

## Deliverables Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Phase 1: Read** | 8 hours | 41 SELECT queries migrated, 15+ unit tests |
| **Phase 2: Create** | 3 hours | 15 INSERT queries migrated, 10+ unit tests |
| **Phase 3: Update** | 3 hours | 15 UPDATE queries migrated, 10+ unit tests |
| **Phase 4: Delete** | 1 hour | 10 DELETE queries migrated, 5+ unit tests |
| **Phase 5: Aggregate** | 2 hours | 20+ aggregate queries, 8+ unit tests |
| **Phase 6: Complex** | 2 hours | 15+ complex/join queries, 8+ unit tests |
| **Refactoring** | 2 hours | Clean up database.py, remove duplicates |
| **Total** | **16 hours** | **50+ unit tests, database.py reduced to ~1,800 lines** |

---

## Success Metrics

- ✅ All 81 CRUD operations migrated to ORM
- ✅ 100% of SELECT queries use SQLAlchemy
- ✅ 100% of INSERT queries use SQLAlchemy
- ✅ 100% of UPDATE queries use SQLAlchemy
- ✅ 100% of DELETE queries use SQLAlchemy
- ✅ 50+ unit tests all passing
- ✅ database.py reduced from 3,003 to ~1,800 lines
- ✅ Functions maintain same API (backward compatible)
- ✅ Performance overhead < 20%
- ✅ All existing API tests still pass

---

## References

- SQLAlchemy Docs: https://docs.sqlalchemy.org/en/20/
- ORM Models: `/orm/models/`
- Current Implementation: `/database.py`
- Tests: `/tests/orm/`
- Pydantic Schemas: `/models/`

