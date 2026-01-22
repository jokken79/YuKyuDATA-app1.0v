"""
ORM-based Database Operations - Phase 2 Migration
===================================================

This module provides SQLAlchemy ORM implementations of all database functions
in database.py. Functions maintain the same signature and return types as the
original raw SQL implementations for backward compatibility.

Migration Status: Phase 1 - Read Operations (41 queries)

Key Patterns:
- All functions use SessionLocal() from orm/__init__.py
- Return types match original: dict (single), list of dict, or scalar
- All queries use proper ORM filters and aggregations
- Supports both SQLite and PostgreSQL via SQLAlchemy

Structure:
1. Session Management Utilities
2. PHASE 1: Read Operations (SELECT)
3. PHASE 2: Create Operations (INSERT)
4. PHASE 3: Update Operations (UPDATE)
5. PHASE 4: Delete Operations (DELETE)
6. PHASE 5: Aggregate Operations
7. PHASE 6: Complex/Join Operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

# Import ORM models
from orm import SessionLocal
from orm.models import (
    Employee,
    LeaveRequest,
    YukyuUsageDetail,
    GenzaiEmployee,
    UkeoiEmployee,
    StaffEmployee,
    User,
    Notification,
    NotificationRead,
    AuditLog,
)


# ============================================
# UTILITY: SESSION MANAGEMENT
# ============================================

@contextmanager
def get_orm_session() -> Session:
    """
    Context manager for ORM sessions.
    Ensures proper cleanup and error handling.

    Usage:
        with get_orm_session() as session:
            employees = session.query(Employee).filter_by(year=2025).all()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ============================================
# PHASE 1: READ OPERATIONS (SELECT)
# ============================================

# Subtask 1.1: Basic Employee Reads

def get_employees_orm(year: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all employees, optionally filtered by year.

    ORM: SELECT * FROM employees WHERE year = ? (if year provided)
    Returns: List of dicts with all employee fields
    """
    with get_orm_session() as session:
        query = session.query(Employee)
        if year:
            query = query.filter_by(year=year)
        results = query.all()
        return [emp.to_dict() for emp in results]


def get_employee_orm(employee_num: str, year: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific employee record.

    ORM: SELECT * FROM employees WHERE employee_num = ? AND year = ?
    Returns: Single employee dict or None
    """
    with get_orm_session() as session:
        emp = session.query(Employee).filter_by(
            employee_num=employee_num,
            year=year
        ).first()
        return emp.to_dict() if emp else None


def get_available_years_orm() -> List[int]:
    """
    Get distinct years available in employee data.

    ORM: SELECT DISTINCT YEAR FROM employees ORDER BY YEAR DESC
    Returns: List of years
    """
    with get_orm_session() as session:
        years = session.query(Employee.year).distinct().order_by(
            Employee.year.desc()
        ).all()
        return [y[0] for y in years]


def get_employees_enhanced_orm(
    year: Optional[int] = None,
    active_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get employees with type (genzai/ukeoi/staff) and active status.
    Crosses employees table with genzai and ukeoi for employment details.

    Returns: List of dicts with extra fields: employee_type, employment_status, is_active
    """
    with get_orm_session() as session:
        # OPTIMIZED: Pre-load all genzai and ukeoi in 2 queries (O(1) instead of O(N))
        # This fixes N+1 query pattern - from 1 + 2*N queries to just 3 queries
        genzai_index = {g.employee_num: g for g in session.query(GenzaiEmployee).all()}
        ukeoi_index = {u.employee_num: u for u in session.query(UkeoiEmployee).all()}

        # Get employees (optionally filtered by year)
        query = session.query(Employee)
        if year:
            query = query.filter_by(year=year)
        employees = query.all()

        results = []
        for emp in employees:
            # O(1) lookup in pre-loaded indexes instead of N+1 queries
            genzai = genzai_index.get(emp.employee_num)
            ukeoi = ukeoi_index.get(emp.employee_num)

            if genzai:
                employee_type = 'genzai'
                employment_status = genzai.status or '在職中'
            elif ukeoi:
                employee_type = 'ukeoi'
                employment_status = ukeoi.status or '在職中'
            else:
                employee_type = 'staff'
                employment_status = '在職中'

            is_active = (
                (genzai and genzai.status == '在職中') or
                (ukeoi and ukeoi.status == '在職中') or
                (not genzai and not ukeoi)
            )

            if active_only and not is_active:
                continue

            emp_dict = emp.to_dict()
            emp_dict['employee_type'] = employee_type
            emp_dict['employment_status'] = employment_status
            emp_dict['is_active'] = 1 if is_active else 0

            results.append(emp_dict)

        # Sort by usage_rate descending
        results.sort(key=lambda x: x.get('usage_rate', 0), reverse=True)
        return results


# Subtask 1.2: Leave Request Reads

def get_leave_requests_orm(
    status: Optional[str] = None,
    employee_num: Optional[str] = None,
    year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get leave requests with optional filters.

    ORM: SELECT * FROM leave_requests WHERE [conditions]
    Returns: List of leave request dicts
    """
    with get_orm_session() as session:
        query = session.query(LeaveRequest)

        if status:
            query = query.filter_by(status=status)
        if employee_num:
            query = query.filter_by(employee_num=employee_num)
        if year:
            query = query.filter_by(year=year)

        results = query.all()
        return [req.to_dict() for req in results]


def get_leave_request_orm(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific leave request by ID.

    ORM: SELECT * FROM leave_requests WHERE id = ?
    Returns: Leave request dict or None
    """
    with get_orm_session() as session:
        req = session.query(LeaveRequest).filter_by(id=request_id).first()
        return req.to_dict() if req else None


def get_employee_yukyu_history_orm(
    employee_num: str,
    current_year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get leave request history for an employee.

    ORM: SELECT * FROM leave_requests WHERE employee_num = ? AND [year]
         ORDER BY created_at DESC
    Returns: List of leave requests ordered by creation time
    """
    with get_orm_session() as session:
        query = session.query(LeaveRequest).filter_by(
            employee_num=employee_num
        )

        if current_year:
            query = query.filter_by(year=current_year)

        results = query.order_by(LeaveRequest.created_at.desc()).all()
        return [req.to_dict() for req in results]


def get_pending_approvals_orm() -> List[Dict[str, Any]]:
    """
    Get all pending leave requests.

    ORM: SELECT * FROM leave_requests WHERE status = 'PENDING'
         ORDER BY created_at
    Returns: List of pending leave requests
    """
    with get_orm_session() as session:
        results = session.query(LeaveRequest).filter_by(
            status='PENDING'
        ).order_by(LeaveRequest.created_at).all()
        return [req.to_dict() for req in results]


# Subtask 1.3: Yukyu Usage Detail Reads

def get_yukyu_usage_details_orm(
    employee_num: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get yukyu usage details with optional filters.

    ORM: SELECT * FROM yukyu_usage_details WHERE [conditions]
    Returns: List of usage detail dicts
    """
    with get_orm_session() as session:
        query = session.query(YukyuUsageDetail)

        if employee_num:
            query = query.filter_by(employee_num=employee_num)

        if year or month:
            # Filter by year/month from use_date (format: YYYY-MM-DD)
            if year and month:
                year_month_prefix = f"{year:04d}-{month:02d}"
                query = query.filter(
                    YukyuUsageDetail.use_date.like(f"{year_month_prefix}%")
                )
            elif year:
                year_prefix = f"{year:04d}"
                query = query.filter(
                    YukyuUsageDetail.use_date.like(f"{year_prefix}%")
                )

        results = query.all()
        return [detail.to_dict() for detail in results]


def get_yukyu_usage_detail_orm(detail_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific yukyu usage detail.

    ORM: SELECT * FROM yukyu_usage_details WHERE id = ?
    Returns: Usage detail dict or None
    """
    with get_orm_session() as session:
        detail = session.query(YukyuUsageDetail).filter_by(id=detail_id).first()
        return detail.to_dict() if detail else None


# Subtask 1.4: Notification Reads

def get_notifications_orm(user_id: str) -> List[Dict[str, Any]]:
    """
    Get notifications for a user, ordered by recency.

    ORM: SELECT * FROM notifications WHERE user_id = ?
         ORDER BY created_at DESC
    Returns: List of notification dicts
    """
    with get_orm_session() as session:
        results = session.query(Notification).filter_by(
            user_id=user_id
        ).order_by(Notification.created_at.desc()).all()
        return [notif.to_dict() for notif in results]


def get_notification_orm(notification_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific notification.

    ORM: SELECT * FROM notifications WHERE id = ?
    Returns: Notification dict or None
    """
    with get_orm_session() as session:
        notif = session.query(Notification).filter_by(
            id=notification_id
        ).first()
        return notif.to_dict() if notif else None


def is_notification_read_orm(
    notification_id: str,
    user_id: str
) -> bool:
    """
    Check if a notification has been read by a user.

    ORM: SELECT * FROM notification_reads WHERE notification_id = ? AND user_id = ?
    Returns: True if read, False otherwise
    """
    with get_orm_session() as session:
        read = session.query(NotificationRead).filter_by(
            notification_id=notification_id,
            user_id=user_id
        ).first()
        return read is not None


def get_read_notification_ids_orm(user_id: str) -> set:
    """
    Get set of all read notification IDs for a user.

    ORM: SELECT notification_id FROM notification_reads WHERE user_id = ?
    Returns: Set of notification IDs
    """
    with get_orm_session() as session:
        reads = session.query(NotificationRead.notification_id).filter_by(
            user_id=user_id
        ).all()
        return {r[0] for r in reads}


# Subtask 1.5: User & Auth Reads

def get_user_orm(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by ID.

    ORM: SELECT * FROM users WHERE id = ?
    Returns: User dict or None
    """
    with get_orm_session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        return user.to_dict() if user else None


def get_user_by_username_orm(username: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by username.

    ORM: SELECT * FROM users WHERE username = ?
    Returns: User dict or None
    """
    with get_orm_session() as session:
        user = session.query(User).filter_by(username=username).first()
        return user.to_dict() if user else None


def get_user_by_email_orm(email: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by email.

    ORM: SELECT * FROM users WHERE email = ?
    Returns: User dict or None
    """
    with get_orm_session() as session:
        user = session.query(User).filter_by(email=email).first()
        return user.to_dict() if user else None


def get_all_users_orm() -> List[Dict[str, Any]]:
    """
    Get all users.

    ORM: SELECT * FROM users
    Returns: List of user dicts
    """
    with get_orm_session() as session:
        results = session.query(User).all()
        return [user.to_dict() for user in results]


# Subtask 1.6: Audit Log Reads

def get_audit_log_orm(
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get audit log entries with pagination.

    ORM: SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ? OFFSET ?
    Returns: List of audit log dicts
    """
    with get_orm_session() as session:
        results = session.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).offset(offset).limit(limit).all()
        return [log.to_dict() for log in results]


def get_audit_log_by_user_orm(
    user_id: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get audit log entries for a specific user.

    ORM: SELECT * FROM audit_log WHERE user_id = ?
         ORDER BY timestamp DESC
    Returns: List of audit log dicts
    """
    with get_orm_session() as session:
        results = session.query(AuditLog).filter_by(
            user_id=user_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [log.to_dict() for log in results]


def get_entity_history_orm(
    entity_type: str,
    entity_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get history of changes to an entity.

    ORM: SELECT * FROM audit_log WHERE entity_type = ? AND entity_id = ?
         ORDER BY timestamp DESC
    Returns: List of audit log dicts for the entity
    """
    with get_orm_session() as session:
        results = session.query(AuditLog).filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [log.to_dict() for log in results]


# ============================================
# ADDITIONAL EMPLOYEE TYPE READS
# ============================================

def get_genzai_orm(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """
    Get dispatch employees (genzai).

    ORM: SELECT * FROM genzai WHERE [conditions]
    Returns: List of genzai employee dicts
    """
    with get_orm_session() as session:
        query = session.query(GenzaiEmployee)

        if status:
            query = query.filter_by(status=status)
        if year:
            # Filter by hire_date and leave_date
            query = query.filter(
                and_(
                    GenzaiEmployee.hire_date <= f"{year:04d}-12-31",
                    or_(
                        GenzaiEmployee.leave_date.is_(None),
                        GenzaiEmployee.leave_date >= f"{year:04d}-01-01"
                    )
                )
            )

        results = query.all()
        return [emp.to_dict() for emp in results]


def get_ukeoi_orm(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """
    Get contractor employees (ukeoi).

    ORM: SELECT * FROM ukeoi WHERE [conditions]
    Returns: List of ukeoi employee dicts
    """
    with get_orm_session() as session:
        query = session.query(UkeoiEmployee)

        if status:
            query = query.filter_by(status=status)
        if year:
            query = query.filter(
                and_(
                    UkeoiEmployee.hire_date <= f"{year:04d}-12-31",
                    or_(
                        UkeoiEmployee.leave_date.is_(None),
                        UkeoiEmployee.leave_date >= f"{year:04d}-01-01"
                    )
                )
            )

        results = query.all()
        return [emp.to_dict() for emp in results]


def get_staff_orm(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """
    Get office staff employees.

    ORM: SELECT * FROM staff WHERE [conditions]
    Returns: List of staff employee dicts
    """
    with get_orm_session() as session:
        query = session.query(StaffEmployee)

        if status:
            query = query.filter_by(status=status)

        results = query.all()
        return [emp.to_dict() for emp in results]


# ============================================
# PHASE 2: CREATE OPERATIONS (INSERT)
# ============================================

def create_leave_request_orm(
    employee_num: str,
    employee_name: str,
    start_date: str,
    end_date: str,
    days_requested: float,
    reason: str,
    year: int,
    hourly_wage: Optional[float] = None,
    leave_type: str = 'full'
) -> Dict[str, Any]:
    """
    Create a new leave request.

    ORM: INSERT INTO leave_requests VALUES (...)
    Returns: Created leave request dict with ID
    """
    with get_orm_session() as session:
        leave_req = LeaveRequest(
            employee_num=employee_num,
            employee_name=employee_name,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=reason,
            year=year,
            hourly_wage=hourly_wage,
            leave_type=leave_type,
            status='PENDING'
        )
        session.add(leave_req)
        session.commit()
        session.refresh(leave_req)
        return leave_req.to_dict()


def add_single_yukyu_usage_orm(
    employee_num: str,
    name: str,
    use_date: str,
    days_used: float = 1.0
) -> Dict[str, Any]:
    """
    Add a single yukyu usage record.

    ORM: INSERT INTO yukyu_usage_details VALUES (...)
    Returns: Created usage detail dict
    """
    with get_orm_session() as session:
        detail = YukyuUsageDetail(
            employee_num=employee_num,
            use_date=use_date,
            days_used=days_used
        )
        session.add(detail)
        session.commit()
        session.refresh(detail)
        return detail.to_dict()


def save_yukyu_usage_details_orm(usage_details_list: List[Dict]) -> int:
    """
    Bulk insert yukyu usage details.

    ORM: bulk_insert_mappings for high-volume inserts
    Returns: Number of records inserted
    """
    with get_orm_session() as session:
        # Prepare data for bulk insert
        details = []
        for detail in usage_details_list:
            details.append(YukyuUsageDetail(
                employee_num=detail.get('employee_num'),
                use_date=detail.get('use_date'),
                days_used=detail.get('days_used', 1.0)
            ))

        session.bulk_save_objects(details)
        session.commit()
        return len(details)


# ============================================
# PHASE 3: UPDATE OPERATIONS (UPDATE)
# ============================================

def update_employee_orm(
    employee_num: str,
    year: int,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Update employee vacation data.

    ORM: UPDATE employees SET [fields] WHERE employee_num = ? AND year = ?
    Returns: Updated employee dict or None if not found
    """
    with get_orm_session() as session:
        emp = session.query(Employee).filter_by(
            employee_num=employee_num,
            year=year
        ).first()

        if not emp:
            return None

        # Update allowed fields
        allowed_fields = {'granted', 'used', 'balance', 'expired', 'usage_rate', 'name', 'haken'}
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(emp, key, value)

        session.commit()
        session.refresh(emp)
        return emp.to_dict()


def approve_leave_request_orm(
    request_id: str,
    approved_by: str
) -> Optional[Dict[str, Any]]:
    """
    Approve a leave request.

    Updates status to APPROVED and records approver.
    Note: Balance deduction should be handled separately.

    ORM: UPDATE leave_requests SET status = 'APPROVED', approver = ?, approved_at = NOW()
    Returns: Updated leave request dict
    """
    with get_orm_session() as session:
        req = session.query(LeaveRequest).filter_by(id=request_id).first()

        if not req:
            return None

        req.status = 'APPROVED'
        req.approver = approved_by
        req.approved_at = datetime.utcnow()

        session.commit()
        session.refresh(req)
        return req.to_dict()


def reject_leave_request_orm(
    request_id: str,
    approved_by: str
) -> Optional[Dict[str, Any]]:
    """
    Reject a leave request.

    ORM: UPDATE leave_requests SET status = 'REJECTED', approver = ?, approved_at = NOW()
    Returns: Updated leave request dict
    """
    with get_orm_session() as session:
        req = session.query(LeaveRequest).filter_by(id=request_id).first()

        if not req:
            return None

        req.status = 'REJECTED'
        req.approver = approved_by
        req.approved_at = datetime.utcnow()

        session.commit()
        session.refresh(req)
        return req.to_dict()


def cancel_leave_request_orm(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Cancel a leave request.

    ORM: UPDATE leave_requests SET status = 'CANCELLED'
    Returns: Updated leave request dict
    """
    with get_orm_session() as session:
        req = session.query(LeaveRequest).filter_by(id=request_id).first()

        if not req:
            return None

        req.status = 'CANCELLED'
        session.commit()
        session.refresh(req)
        return req.to_dict()


def revert_approved_request_orm(
    request_id: str,
    reverted_by: str = "Manager"
) -> Optional[Dict[str, Any]]:
    """
    Revert an approved leave request back to PENDING.

    ORM: UPDATE leave_requests SET status = 'REVERTED', approver = ?
    Returns: Updated leave request dict
    """
    with get_orm_session() as session:
        req = session.query(LeaveRequest).filter_by(id=request_id).first()

        if not req:
            return None

        # Only revert if currently APPROVED
        if req.status != 'APPROVED':
            return req.to_dict()

        req.status = 'REVERTED'
        req.approver = reverted_by

        session.commit()
        session.refresh(req)
        return req.to_dict()


def update_yukyu_usage_detail_orm(
    detail_id: int,
    days_used: Optional[float] = None,
    use_date: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update a yukyu usage detail.

    ORM: UPDATE yukyu_usage_details SET days_used = ?, use_date = ? WHERE id = ?
    Returns: Updated detail dict or None
    """
    with get_orm_session() as session:
        detail = session.query(YukyuUsageDetail).filter_by(id=detail_id).first()

        if not detail:
            return None

        if days_used is not None:
            detail.days_used = days_used
        if use_date is not None:
            detail.use_date = use_date

        session.commit()
        session.refresh(detail)
        return detail.to_dict()


# ============================================
# PHASE 4: DELETE OPERATIONS (DELETE)
# ============================================

def delete_yukyu_usage_detail_orm(detail_id: int) -> bool:
    """
    Delete a yukyu usage detail.

    ORM: DELETE FROM yukyu_usage_details WHERE id = ?
    Returns: True if deleted, False if not found
    """
    with get_orm_session() as session:
        detail = session.query(YukyuUsageDetail).filter_by(id=detail_id).first()

        if not detail:
            return False

        session.delete(detail)
        session.commit()
        return True


def clear_employees_orm() -> int:
    """
    Clear all employee records.

    ORM: DELETE FROM employees
    Returns: Number of records deleted
    """
    with get_orm_session() as session:
        count = session.query(Employee).delete()
        session.commit()
        return count


def clear_genzai_orm() -> int:
    """Clear all genzai records."""
    with get_orm_session() as session:
        count = session.query(GenzaiEmployee).delete()
        session.commit()
        return count


def clear_ukeoi_orm() -> int:
    """Clear all ukeoi records."""
    with get_orm_session() as session:
        count = session.query(UkeoiEmployee).delete()
        session.commit()
        return count


def clear_staff_orm() -> int:
    """Clear all staff records."""
    with get_orm_session() as session:
        count = session.query(StaffEmployee).delete()
        session.commit()
        return count


def clear_yukyu_usage_details_orm() -> int:
    """Clear all yukyu usage details."""
    with get_orm_session() as session:
        count = session.query(YukyuUsageDetail).delete()
        session.commit()
        return count


# ============================================
# PHASE 5: AGGREGATE OPERATIONS
# ============================================

def get_unread_count_orm(user_id: str) -> int:
    """
    Get count of unread notifications for a user.

    ORM: SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0
    Returns: Count of unread notifications
    """
    with get_orm_session() as session:
        count = session.query(func.count(Notification.id)).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == 0
            )
        ).scalar()
        return count or 0


def get_total_balance_orm(employee_num: str, year: int) -> float:
    """
    Get total accumulated balance for an employee.

    ORM: SELECT COALESCE(SUM(balance), 0) FROM employees
         WHERE employee_num = ? AND year >= ?
    Returns: Total balance
    """
    with get_orm_session() as session:
        total = session.query(func.sum(Employee.balance)).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year >= year - 1  # Current + previous year
            )
        ).scalar()
        return total or 0.0


def get_employee_count_by_year_orm(year: int) -> int:
    """
    Count employees in a given year.

    ORM: SELECT COUNT(*) FROM employees WHERE year = ?
    Returns: Employee count
    """
    with get_orm_session() as session:
        count = session.query(func.count(Employee.id)).filter(
            Employee.year == year
        ).scalar()
        return count or 0


def get_leave_request_count_by_status_orm(year: Optional[int] = None) -> Dict[str, int]:
    """
    Count leave requests by status.

    ORM: SELECT status, COUNT(*) FROM leave_requests GROUP BY status
    Returns: Dict mapping status to count
    """
    with get_orm_session() as session:
        query = session.query(
            LeaveRequest.status,
            func.count(LeaveRequest.id)
        ).group_by(LeaveRequest.status)

        if year:
            query = query.filter(LeaveRequest.year == year)

        results = query.all()
        return {status: count for status, count in results}


def get_average_usage_rate_orm(year: int) -> float:
    """
    Get average usage rate for all employees.

    ORM: SELECT AVG(usage_rate) FROM employees WHERE year = ?
    Returns: Average usage rate
    """
    with get_orm_session() as session:
        avg = session.query(func.avg(Employee.usage_rate)).filter(
            Employee.year == year
        ).scalar()
        return float(avg) if avg else 0.0


# ============================================
# PHASE 6: COMPLEX OPERATIONS
# ============================================

def get_leave_requests_with_employee_orm(year: int) -> List[Dict[str, Any]]:
    """
    Get leave requests with employee details via join.

    ORM: SELECT lr.*, e.name, e.haken FROM leave_requests lr
         JOIN employees e ON lr.employee_num = e.employee_num
    Returns: List of leave requests with employee fields
    """
    with get_orm_session() as session:
        results = session.query(
            LeaveRequest,
            Employee.name,
            Employee.haken
        ).join(
            Employee,
            and_(
                LeaveRequest.employee_num == Employee.employee_num,
                LeaveRequest.year == Employee.year
            )
        ).filter(LeaveRequest.year == year).all()

        # Combine results
        combined = []
        for req, emp_name, emp_haken in results:
            req_dict = req.to_dict()
            req_dict['employee_name'] = emp_name
            req_dict['workplace'] = emp_haken
            combined.append(req_dict)

        return combined


def get_notifications_with_read_status_orm(user_id: str) -> List[Dict[str, Any]]:
    """
    Get notifications with read status indicators.

    ORM: SELECT n.*, nr.read_at FROM notifications n
         LEFT JOIN notification_reads nr ON n.id = nr.notification_id
         WHERE n.user_id = ?
    Returns: List of notifications with is_read flag
    """
    with get_orm_session() as session:
        notifications = session.query(Notification).filter_by(
            user_id=user_id
        ).order_by(Notification.created_at.desc()).all()

        # Get read set
        read_ids = get_read_notification_ids_orm(user_id)

        results = []
        for notif in notifications:
            notif_dict = notif.to_dict()
            notif_dict['is_read'] = notif.id in read_ids
            results.append(notif_dict)

        return results


def get_audit_log_stats_orm(days: int = 30) -> Dict[str, Any]:
    """
    Get statistics on audit log from past N days.

    ORM: SELECT entity_type, COUNT(*), action FROM audit_log
         WHERE timestamp >= NOW() - INTERVAL ? DAY
         GROUP BY entity_type, action
    Returns: Dict with statistics
    """
    with get_orm_session() as session:
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get activity by entity type
        entity_counts = session.query(
            AuditLog.entity_type,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.timestamp >= cutoff_date
        ).group_by(AuditLog.entity_type).all()

        # Get activity by action
        action_counts = session.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.timestamp >= cutoff_date
        ).group_by(AuditLog.action).all()

        # Get top users
        top_users = session.query(
            AuditLog.user_id,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.timestamp >= cutoff_date
        ).group_by(AuditLog.user_id).order_by(
            func.count(AuditLog.id).desc()
        ).limit(10).all()

        return {
            'period_days': days,
            'entity_types': dict(entity_counts),
            'actions': dict(action_counts),
            'top_users': [{
                'user_id': user_id,
                'action_count': count
            } for user_id, count in top_users],
            'total_actions': sum(count for _, count in entity_counts)
        }
