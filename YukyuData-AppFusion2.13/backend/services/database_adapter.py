"""
Database Adapter - Abstraction Layer
=====================================

This module provides a unified interface for database operations.
All calls delegate directly to the database/ package, which handles
connections, queries, and transactions internally.

Usage:
    from services.database_adapter import get_employees, approve_leave_request

    employees = get_employees(year=2025)
    approve_leave_request(request_id=123, approved_by="admin")

Environment Variables:
    LOG_LEVEL=DEBUG - Show detailed logging for each function call
"""

import os
import logging
from typing import Optional, List, Dict, Any
from functools import wraps

# Setup logging
logger = logging.getLogger(__name__)
log_level = os.getenv("LOG_LEVEL", "INFO")
logger.setLevel(getattr(logging, log_level, logging.INFO))

logger.info("Database Adapter initialized. All calls delegate to database/ package.")


# ============================================================================
# IMPORTS
# ============================================================================

import database


# ============================================================================
# DECORATOR: Track implementation usage
# ============================================================================

def track_implementation(func_name: str):
    """
    Decorator to log function calls for debugging and monitoring.

    Args:
        func_name: Name of the logical function (e.g., "get_employees")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug("Calling %s() with args=%s, kwargs=%s", func_name, args, kwargs)
            try:
                result = func(*args, **kwargs)
                logger.debug("%s() completed successfully", func_name)
                return result
            except Exception as e:
                logger.error("%s() failed: %s", func_name, e, exc_info=True)
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
    """
    logger.debug("get_employees(year=%s, active_only=%s)", year, active_only)
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
    """
    logger.debug("get_employee(employee_num=%s, year=%s)", employee_num, year)
    return database.get_employee_by_num_year(employee_num=employee_num, year=year)


def get_available_years() -> List[int]:
    """
    Get list of all years available in the database.

    Returns:
        List of years (e.g., [2023, 2024, 2025])
    """
    logger.debug("get_available_years()")
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
    """
    logger.debug("get_employees_enhanced(year=%s, active_only=%s)", year, active_only)
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
    """
    logger.debug("save_employee(%s)", employee_data.get('id'))
    database.save_employees([employee_data])


def save_employees(employees_data: List[Dict[str, Any]]) -> None:
    """
    Save or update multiple employee records (batch operation).

    Args:
        employees_data: List of employee data dictionaries
    """
    if not employees_data:
        logger.warning("save_employees called with empty list")
        return

    logger.debug("save_employees (batch, count=%d)", len(employees_data))
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
    """
    logger.debug("get_leave_requests(status=%s, employee_num=%s, year=%s)", status, employee_num, year)
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
    """
    logger.debug("get_leave_request(request_id=%s)", request_id)
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
    """
    logger.info("approve_leave_request(request_id=%s, approved_by=%s)", request_id, approved_by)
    return database.approve_leave_request(request_id=request_id, approved_by=approved_by)


def reject_leave_request(request_id: int, approved_by: str) -> bool:
    """
    Reject a leave request (no balance changes).

    Args:
        request_id: Leave request ID
        approved_by: User ID of approver

    Returns:
        True if successful, raises ValueError otherwise
    """
    logger.info("reject_leave_request(request_id=%s, approved_by=%s)", request_id, approved_by)
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
    """
    logger.debug("get_employee_yukyu_history(employee_num=%s, current_year=%s)", employee_num, current_year)
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
    """
    logger.debug("get_employee_total_balance(employee_num=%s, year=%s)", employee_num, year)
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
    """
    logger.debug("get_genzai(status=%s, year=%s, active_in_year=%s)", status, year, active_in_year)
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
    """
    if not genzai_data:
        logger.warning("save_genzai called with empty list")
        return

    logger.debug("save_genzai (batch, count=%d)", len(genzai_data))
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
    """
    logger.debug("get_ukeoi(status=%s, year=%s, active_in_year=%s)", status, year, active_in_year)
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
    """
    if not ukeoi_data:
        logger.warning("save_ukeoi called with empty list")
        return

    logger.debug("save_ukeoi (batch, count=%d)", len(ukeoi_data))
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
    """
    logger.debug("get_staff(status=%s, year=%s, active_in_year=%s)", status, year, active_in_year)
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
    """
    if not staff_data:
        logger.warning("save_staff called with empty list")
        return

    logger.debug("save_staff (batch, count=%d)", len(staff_data))
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
    """
    logger.debug("get_yukyu_usage_details(employee_num=%s, year=%s, month=%s)", employee_num, year, month)
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
    """
    if not usage_details_list:
        logger.warning("save_yukyu_usage_details called with empty list")
        return

    logger.debug("save_yukyu_usage_details (batch, count=%d)", len(usage_details_list))
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
    """
    logger.debug("get_monthly_usage_summary(year=%s)", year)
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
    """
    logger.debug("get_employee_usage_summary(employee_num=%s, year=%s)", employee_num, year)
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
    """
    logger.debug("get_audit_log(entity_type=%s, entity_id=%s, limit=%s)", entity_type, entity_id, limit)
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
    """
    logger.debug("get_notifications(user_id=%s)", user_id)
    return database.get_notifications(user_id=user_id)


def get_read_notification_ids(user_id: str) -> set:
    """
    Get set of read notification IDs for a user.

    Args:
        user_id: User ID

    Returns:
        Set of read notification IDs
    """
    logger.debug("get_read_notification_ids(user_id=%s)", user_id)
    return database.get_read_notification_ids(user_id=user_id)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_implementation_status() -> Dict[str, Any]:
    """
    Get current implementation status (useful for debugging).

    Returns:
        Dictionary with:
        - implementation: Current implementation name
        - database_type: SQLite or PostgreSQL
        - log_level: Current log level
    """
    db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()

    return {
        "implementation": "database/ package (SQLAlchemy-backed)",
        "database_type": db_type,
        "log_level": log_level,
    }


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    import json
    status = get_implementation_status()
    print("Database Adapter Status:")
    print(json.dumps(status, indent=2))
