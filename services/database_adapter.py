"""
Database Adapter - Abstraction Layer
=====================================

This module provides a unified interface for database operations.
The database/ package now uses SQLAlchemy ORM internally, so this adapter
delegates all calls to the database package.

The USE_ORM flag is kept for backwards compatibility but the database/
package already uses ORM (SessionLocal + SQLAlchemy models) for all operations.

Usage:
    from services.database_adapter import get_employees, approve_leave_request

    employees = get_employees(year=2025)
    approve_leave_request(request_id=123, approved_by="admin")

Environment Variables:
    USE_ORM=false   - Default (production). All calls go through database/ package.
    LOG_LEVEL=DEBUG - Show which implementation each function uses
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from functools import wraps

# Setup logging
logger = logging.getLogger(__name__)
log_level = os.getenv("LOG_LEVEL", "INFO")
logger.setLevel(getattr(logging, log_level, logging.INFO))

# ============================================================================
# FEATURE FLAG: USE_ORM
# ============================================================================

# USE_ORM flag kept for backwards compatibility.
# The database/ package already uses SQLAlchemy ORM internally.
USE_ORM = os.getenv("USE_ORM", "false").lower() in ("true", "1", "yes")

# database_orm.py no longer exists - replaced by database/ package (which uses ORM).
# All adapter functions now delegate to the database package directly.
ORM_AVAILABLE = False

logger.info(f"Database Adapter initialized. All calls delegate to database/ package (ORM-based).")


# ============================================================================
# IMPORTS
# ============================================================================

import database


# ============================================================================
# DECORATOR: Track implementation usage
# ============================================================================

def track_implementation(func_name: str, impl_type: str):
    """
    Decorator to track which implementation is being used.

    Args:
        func_name: Name of the logical function (e.g., "get_employees")
        impl_type: Type of implementation ("orm" or "sql")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"[{impl_type.upper()}] Calling {func_name}() with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"[{impl_type.upper()}] {func_name}() completed successfully")
                return result
            except Exception as e:
                logger.error(f"[{impl_type.upper()}] {func_name}() failed: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# ============================================================================
# ADAPTER FUNCTIONS - Employees (Read)
# ============================================================================

def get_employees(year: Optional[int] = None, active_only: bool = False) -> List[Dict[str, Any]]:
    """
    Get all employees, optionally filtered by year and active status.

    Args:
        year: Filter by fiscal year (optional)
        active_only: Only include active employees (optional)

    Returns:
        List of employee dictionaries

    Implementation:
        - ORM: database_orm.get_employees_orm()
        - SQL: database.get_employees() + database.get_employees_enhanced()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_employees(year={year}, active_only={active_only})")
        return database_orm.get_employees_orm(year=year)
    else:
        logger.debug(f"[SQL] get_employees(year={year}, active_only={active_only})")
        if active_only:
            return database.get_employees_enhanced(year=year, active_only=True)
        return database.get_employees(year=year)


def get_employee(employee_num: str, year: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific employee record by employee number and year.

    Args:
        employee_num: Employee number (e.g., "001")
        year: Fiscal year (e.g., 2025)

    Returns:
        Employee dictionary or None if not found

    Implementation:
        - ORM: database_orm.get_employee_orm()
        - SQL: database.get_employee_by_num_year()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_employee(employee_num={employee_num}, year={year})")
        return database_orm.get_employee_orm(employee_num=employee_num, year=year)
    else:
        logger.debug(f"[SQL] get_employee(employee_num={employee_num}, year={year})")
        return database.get_employee_by_num_year(employee_num=employee_num, year=year)


def get_available_years() -> List[int]:
    """
    Get list of all years available in the database.

    Returns:
        List of years (e.g., [2023, 2024, 2025])

    Implementation:
        - ORM: database_orm.get_available_years_orm()
        - SQL: database.get_available_years()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug("[ORM] get_available_years()")
        return database_orm.get_available_years_orm()
    else:
        logger.debug("[SQL] get_available_years()")
        return database.get_available_years()


def get_employees_enhanced(year: Optional[int] = None, active_only: bool = False) -> List[Dict[str, Any]]:
    """
    Get employees with enhanced information (type, kana, employment status).

    Args:
        year: Filter by fiscal year (optional)
        active_only: Only active employees (optional)

    Returns:
        List of enhanced employee dictionaries with fields:
        - employee_type (genzai/ukeoi/staff)
        - employment_status (在職中/退職)
        - is_active (boolean)
        - kana (カナ name)

    Implementation:
        - ORM: database_orm.get_employees_enhanced_orm()
        - SQL: database.get_employees_enhanced()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_employees_enhanced(year={year}, active_only={active_only})")
        return database_orm.get_employees_enhanced_orm(year=year, active_only=active_only)
    else:
        logger.debug(f"[SQL] get_employees_enhanced(year={year}, active_only={active_only})")
        return database.get_employees_enhanced(year=year, active_only=active_only)


# ============================================================================
# ADAPTER FUNCTIONS - Employees (Write)
# ============================================================================

def save_employee(employee_data: Dict[str, Any]) -> None:
    """
    Save or update a single employee record.

    Args:
        employee_data: Employee data dictionary with keys:
            - id: {employee_num}_{year}
            - employee_num: Employee number
            - name: Employee name
            - granted: Days granted
            - used: Days used
            - balance: Days remaining
            - year: Fiscal year

    Implementation:
        - ORM: Uses database_orm save operations (Phase 2)
        - SQL: Uses database.save_employees()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] save_employee({employee_data.get('id')})")
        # ORM implementation would go here in Phase 2
        logger.warning("[ORM] save_employee not yet implemented in ORM. Falling back to SQL.")
        database.save_employees([employee_data])
    else:
        logger.debug(f"[SQL] save_employee({employee_data.get('id')})")
        database.save_employees([employee_data])


def save_employees(employees_data: List[Dict[str, Any]]) -> None:
    """
    Save or update multiple employee records (batch operation).

    Args:
        employees_data: List of employee data dictionaries

    Implementation:
        - ORM: Uses batch ORM operations (Phase 2)
        - SQL: Uses database.save_employees()
    """
    if not employees_data:
        logger.warning("save_employees called with empty list")
        return

    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] save_employees (batch, count={len(employees_data)})")
        # ORM batch implementation would go here in Phase 2
        logger.warning("[ORM] save_employees batch not yet implemented. Falling back to SQL.")
        database.save_employees(employees_data)
    else:
        logger.debug(f"[SQL] save_employees (batch, count={len(employees_data)})")
        database.save_employees(employees_data)


# ============================================================================
# ADAPTER FUNCTIONS - Leave Requests (Read)
# ============================================================================

def get_leave_requests(
    status: Optional[str] = None,
    employee_num: Optional[str] = None,
    year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get leave requests with optional filters.

    Args:
        status: Filter by status (PENDING, APPROVED, REJECTED)
        employee_num: Filter by employee number
        year: Filter by fiscal year

    Returns:
        List of leave request dictionaries

    Implementation:
        - ORM: database_orm.get_leave_requests_orm()
        - SQL: database.get_leave_requests()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_leave_requests(status={status}, employee_num={employee_num}, year={year})")
        return database_orm.get_leave_requests_orm(
            status=status,
            employee_num=employee_num,
            year=year
        )
    else:
        logger.debug(f"[SQL] get_leave_requests(status={status}, employee_num={employee_num}, year={year})")
        return database.get_leave_requests(
            status=status,
            employee_num=employee_num,
            year=year
        )


def get_leave_request(request_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a specific leave request by ID.

    Args:
        request_id: Leave request ID

    Returns:
        Leave request dictionary or None if not found

    Implementation:
        - ORM: database_orm.get_leave_request_orm()
        - SQL: database.get_leave_requests() then filter
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_leave_request(request_id={request_id})")
        return database_orm.get_leave_request_orm(request_id=str(request_id))
    else:
        logger.debug(f"[SQL] get_leave_request(request_id={request_id})")
        # Fallback: query all and filter (not ideal for production)
        all_requests = database.get_leave_requests()
        for req in all_requests:
            if req.get('id') == request_id:
                return req
        return None


# ============================================================================
# ADAPTER FUNCTIONS - Leave Requests (Write)
# ============================================================================

def approve_leave_request(request_id: int, approved_by: str) -> bool:
    """
    Approve a leave request and deduct days from employee balance (LIFO).

    Args:
        request_id: Leave request ID
        approved_by: User ID of approver

    Returns:
        True if successful, raises ValueError otherwise

    Behavior:
        - Marks request as APPROVED
        - Calls fiscal_year.apply_lifo_deduction() to deduct days
        - Updates employee balance and usage_rate
        - Logs to audit trail

    Implementation:
        - ORM: database_orm.approve_leave_request_orm()
        - SQL: database.approve_leave_request()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.info(f"[ORM] approve_leave_request(request_id={request_id}, approved_by={approved_by})")
        return database_orm.approve_leave_request_orm(
            request_id=str(request_id),
            approved_by=approved_by
        )
    else:
        logger.info(f"[SQL] approve_leave_request(request_id={request_id}, approved_by={approved_by})")
        return database.approve_leave_request(request_id=request_id, approved_by=approved_by)


def reject_leave_request(request_id: int, approved_by: str) -> bool:
    """
    Reject a leave request (no balance changes).

    Args:
        request_id: Leave request ID
        approved_by: User ID of approver

    Returns:
        True if successful, raises ValueError otherwise

    Implementation:
        - ORM: database_orm.reject_leave_request_orm()
        - SQL: database.reject_leave_request()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.info(f"[ORM] reject_leave_request(request_id={request_id}, approved_by={approved_by})")
        return database_orm.reject_leave_request_orm(
            request_id=str(request_id),
            approved_by=approved_by
        )
    else:
        logger.info(f"[SQL] reject_leave_request(request_id={request_id}, approved_by={approved_by})")
        return database.reject_leave_request(request_id=request_id, approved_by=approved_by)


# ============================================================================
# ADAPTER FUNCTIONS - Employee History
# ============================================================================

def get_employee_yukyu_history(
    employee_num: str,
    current_year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get employee's vacation history (current and previous year).

    Follows Japanese law: only keep last 2 years of vacation data.

    Args:
        employee_num: Employee number
        current_year: Year to use as reference (default: current year)

    Returns:
        List of employee records for current year and previous year

    Implementation:
        - ORM: database_orm.get_employee_yukyu_history_orm()
        - SQL: database.get_employee_yukyu_history()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_employee_yukyu_history(employee_num={employee_num}, current_year={current_year})")
        return database_orm.get_employee_yukyu_history_orm(
            employee_num=employee_num,
            current_year=current_year
        )
    else:
        logger.debug(f"[SQL] get_employee_yukyu_history(employee_num={employee_num}, current_year={current_year})")
        return database.get_employee_yukyu_history(
            employee_num=employee_num,
            current_year=current_year
        )


def get_employee_total_balance(employee_num: str, year: int) -> float:
    """
    Get total vacation balance for an employee in a specific year.

    Args:
        employee_num: Employee number
        year: Fiscal year

    Returns:
        Total remaining days

    Implementation:
        - ORM: database_orm.get_total_balance_orm()
        - SQL: database.get_employee_total_balance()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_employee_total_balance(employee_num={employee_num}, year={year})")
        return database_orm.get_total_balance_orm(
            employee_num=employee_num,
            year=year
        )
    else:
        logger.debug(f"[SQL] get_employee_total_balance(employee_num={employee_num}, year={year})")
        return database.get_employee_total_balance(
            employee_num=employee_num,
            year=year
        )


# ============================================================================
# ADAPTER FUNCTIONS - Dispatch Employees (Genzai)
# ============================================================================

def get_genzai(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """
    Get dispatch employees (派遣社員).

    Args:
        status: Filter by status (在職中/退職)
        year: Filter by year
        active_in_year: Only active employees in specified year

    Returns:
        List of genzai employee dictionaries

    Implementation:
        - ORM: database_orm.get_genzai_orm()
        - SQL: database.get_genzai()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_genzai(status={status}, year={year}, active_in_year={active_in_year})")
        return database_orm.get_genzai_orm(
            status=status,
            year=year,
            active_in_year=active_in_year
        )
    else:
        logger.debug(f"[SQL] get_genzai(status={status}, year={year}, active_in_year={active_in_year})")
        return database.get_genzai(
            status=status,
            year=year,
            active_in_year=active_in_year
        )


def save_genzai(genzai_data: List[Dict[str, Any]]) -> None:
    """
    Save or update dispatch employees (派遣社員).

    Args:
        genzai_data: List of genzai employee data

    Implementation:
        - ORM: Uses batch ORM operations (Phase 2)
        - SQL: database.save_genzai()
    """
    if not genzai_data:
        logger.warning("save_genzai called with empty list")
        return

    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] save_genzai (batch, count={len(genzai_data)})")
        logger.warning("[ORM] save_genzai not yet implemented. Falling back to SQL.")
        database.save_genzai(genzai_data)
    else:
        logger.debug(f"[SQL] save_genzai (batch, count={len(genzai_data)})")
        database.save_genzai(genzai_data)


# ============================================================================
# ADAPTER FUNCTIONS - Contract Employees (Ukeoi)
# ============================================================================

def get_ukeoi(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """
    Get contract employees (請負社員).

    Args:
        status: Filter by status (在職中/退職)
        year: Filter by year
        active_in_year: Only active employees in specified year

    Returns:
        List of ukeoi employee dictionaries

    Implementation:
        - ORM: database_orm.get_ukeoi_orm()
        - SQL: database.get_ukeoi()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_ukeoi(status={status}, year={year}, active_in_year={active_in_year})")
        return database_orm.get_ukeoi_orm(
            status=status,
            year=year,
            active_in_year=active_in_year
        )
    else:
        logger.debug(f"[SQL] get_ukeoi(status={status}, year={year}, active_in_year={active_in_year})")
        return database.get_ukeoi(
            status=status,
            year=year,
            active_in_year=active_in_year
        )


def save_ukeoi(ukeoi_data: List[Dict[str, Any]]) -> None:
    """
    Save or update contract employees (請負社員).

    Args:
        ukeoi_data: List of ukeoi employee data

    Implementation:
        - ORM: Uses batch ORM operations (Phase 2)
        - SQL: database.save_ukeoi()
    """
    if not ukeoi_data:
        logger.warning("save_ukeoi called with empty list")
        return

    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] save_ukeoi (batch, count={len(ukeoi_data)})")
        logger.warning("[ORM] save_ukeoi not yet implemented. Falling back to SQL.")
        database.save_ukeoi(ukeoi_data)
    else:
        logger.debug(f"[SQL] save_ukeoi (batch, count={len(ukeoi_data)})")
        database.save_ukeoi(ukeoi_data)


# ============================================================================
# ADAPTER FUNCTIONS - Staff Employees
# ============================================================================

def get_staff(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """
    Get office staff employees (スタッフ社員).

    Args:
        status: Filter by status (在職中/退職)
        year: Filter by year
        active_in_year: Only active employees in specified year

    Returns:
        List of staff employee dictionaries

    Implementation:
        - ORM: database_orm.get_staff_orm()
        - SQL: database.get_staff()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_staff(status={status}, year={year}, active_in_year={active_in_year})")
        return database_orm.get_staff_orm(
            status=status,
            year=year,
            active_in_year=active_in_year
        )
    else:
        logger.debug(f"[SQL] get_staff(status={status}, year={year}, active_in_year={active_in_year})")
        return database.get_staff(
            status=status,
            year=year,
            active_in_year=active_in_year
        )


def save_staff(staff_data: List[Dict[str, Any]]) -> None:
    """
    Save or update office staff employees (スタッフ社員).

    Args:
        staff_data: List of staff employee data

    Implementation:
        - ORM: Uses batch ORM operations (Phase 2)
        - SQL: database.save_staff()
    """
    if not staff_data:
        logger.warning("save_staff called with empty list")
        return

    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] save_staff (batch, count={len(staff_data)})")
        logger.warning("[ORM] save_staff not yet implemented. Falling back to SQL.")
        database.save_staff(staff_data)
    else:
        logger.debug(f"[SQL] save_staff (batch, count={len(staff_data)})")
        database.save_staff(staff_data)


# ============================================================================
# ADAPTER FUNCTIONS - Yukyu Usage Details
# ============================================================================

def get_yukyu_usage_details(
    employee_num: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get individual vacation usage dates (detailed tracking).

    Args:
        employee_num: Filter by employee number
        year: Filter by year
        month: Filter by month (1-12)

    Returns:
        List of usage detail dictionaries

    Implementation:
        - ORM: database_orm.get_yukyu_usage_details_orm()
        - SQL: database.get_yukyu_usage_details()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_yukyu_usage_details(employee_num={employee_num}, year={year}, month={month})")
        return database_orm.get_yukyu_usage_details_orm(
            employee_num=employee_num,
            year=year,
            month=month
        )
    else:
        logger.debug(f"[SQL] get_yukyu_usage_details(employee_num={employee_num}, year={year}, month={month})")
        return database.get_yukyu_usage_details(
            employee_num=employee_num,
            year=year,
            month=month
        )


def save_yukyu_usage_details(usage_details_list: List[Dict[str, Any]]) -> None:
    """
    Save individual vacation usage dates (batch operation).

    Args:
        usage_details_list: List of usage detail dictionaries with keys:
            - employee_num: Employee number
            - name: Employee name
            - use_date: Date of usage (YYYY-MM-DD)
            - year: Year extracted from use_date
            - month: Month extracted from use_date
            - days_used: Number of days (default 1.0)

    Implementation:
        - ORM: database_orm.save_yukyu_usage_details_orm()
        - SQL: database.save_yukyu_usage_details()
    """
    if not usage_details_list:
        logger.warning("save_yukyu_usage_details called with empty list")
        return

    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] save_yukyu_usage_details (batch, count={len(usage_details_list)})")
        database_orm.save_yukyu_usage_details_orm(usage_details_list)
    else:
        logger.debug(f"[SQL] save_yukyu_usage_details (batch, count={len(usage_details_list)})")
        database.save_yukyu_usage_details(usage_details_list)


# ============================================================================
# ADAPTER FUNCTIONS - Analytics & Reports
# ============================================================================

def get_monthly_usage_summary(year: int) -> Dict[int, Dict[str, Any]]:
    """
    Get monthly usage summary for a specific year.

    Returns count of employees and total days used per month.

    Args:
        year: Fiscal year

    Returns:
        Dict with keys 1-12 (months) containing:
        - employee_count: Number of employees who used vacation
        - total_days: Total vacation days used
        - usage_count: Count of usage records

    Implementation:
        - ORM: Via raw SQL aggregation (Phase 2)
        - SQL: database.get_monthly_usage_summary()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_monthly_usage_summary(year={year})")
        logger.warning("[ORM] get_monthly_usage_summary not yet implemented. Falling back to SQL.")
        return database.get_monthly_usage_summary(year=year)
    else:
        logger.debug(f"[SQL] get_monthly_usage_summary(year={year})")
        return database.get_monthly_usage_summary(year=year)


def get_employee_usage_summary(employee_num: str, year: int) -> Optional[Dict[str, Any]]:
    """
    Get vacation usage summary for a specific employee in a year.

    Args:
        employee_num: Employee number
        year: Fiscal year

    Returns:
        Summary dictionary with granted, used, balance, expired, usage_rate
        or None if not found

    Implementation:
        - SQL: database.get_employee_usage_summary()
    """
    logger.debug(f"[SQL] get_employee_usage_summary(employee_num={employee_num}, year={year})")
    return database.get_employee_usage_summary(employee_num=employee_num, year=year)


# ============================================================================
# ADAPTER FUNCTIONS - Audit & Logging
# ============================================================================

def get_audit_log(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get audit log entries.

    Args:
        entity_type: Filter by entity type (e.g., "leave_request", "employee")
        entity_id: Filter by entity ID
        limit: Maximum records to return (default: 100)

    Returns:
        List of audit log dictionaries

    Implementation:
        - ORM: database_orm.get_audit_log_orm()
        - SQL: database.get_audit_log()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_audit_log(entity_type={entity_type}, entity_id={entity_id}, limit={limit})")
        return database_orm.get_audit_log_orm(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )
    else:
        logger.debug(f"[SQL] get_audit_log(entity_type={entity_type}, entity_id={entity_id}, limit={limit})")
        return database.get_audit_log(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit
        )


# ============================================================================
# ADAPTER FUNCTIONS - Notifications
# ============================================================================

def get_notifications(user_id: str) -> List[Dict[str, Any]]:
    """
    Get notifications for a specific user.

    Args:
        user_id: User ID

    Returns:
        List of notification dictionaries

    Implementation:
        - ORM: database_orm.get_notifications_orm()
        - SQL: Falls back to ORM for now (notifications feature)
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_notifications(user_id={user_id})")
        return database_orm.get_notifications_orm(user_id=user_id)
    else:
        logger.debug(f"[SQL] get_notifications(user_id={user_id})")
        if ORM_AVAILABLE:
            return database_orm.get_notifications_orm(user_id=user_id)
        return []


def get_read_notification_ids(user_id: str) -> set:
    """
    Get set of read notification IDs for a user.

    Args:
        user_id: User ID

    Returns:
        Set of read notification IDs

    Implementation:
        - ORM: database_orm.get_read_notification_ids_orm()
        - SQL: database.get_read_notification_ids()
    """
    if USE_ORM and ORM_AVAILABLE:
        logger.debug(f"[ORM] get_read_notification_ids(user_id={user_id})")
        return database_orm.get_read_notification_ids_orm(user_id=user_id)
    else:
        logger.debug(f"[SQL] get_read_notification_ids(user_id={user_id})")
        return database.get_read_notification_ids(user_id=user_id)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_implementation_status() -> Dict[str, Any]:
    """
    Get current implementation status (useful for debugging).

    Returns:
        Dictionary with:
        - use_orm: Whether ORM is enabled
        - orm_available: Whether ORM module is available
        - implementation: Current implementation name
        - database_type: SQLite or PostgreSQL
    """
    db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()

    return {
        "use_orm": USE_ORM,
        "orm_available": ORM_AVAILABLE,
        "implementation": "SQLAlchemy ORM (Phase 2)" if (USE_ORM and ORM_AVAILABLE) else "Raw SQL (database.py)",
        "database_type": db_type,
        "fallback_enabled": True,
        "log_level": log_level,
    }


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Test implementation status
    import json
    status = get_implementation_status()
    print("Database Adapter Status:")
    print(json.dumps(status, indent=2))
