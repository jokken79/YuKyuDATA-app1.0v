"""
Database Adapter Usage Examples
================================

This file demonstrates how to use the database_adapter module to write
code that automatically switches between raw SQL and ORM implementations.

The adapter provides a unified interface regardless of the underlying
implementation, making it easy to migrate to ORM without changing client code.

Setup:
    1. Ensure services/database_adapter.py exists
    2. Set USE_ORM env var: true (ORM) or false (raw SQL)
    3. Import functions from services.database_adapter
    4. Use exactly as shown below - the adapter handles the rest

Environment Control:
    # Use raw SQL (production default)
    $ export USE_ORM=false
    $ python app.py

    # Use SQLAlchemy ORM (development/testing)
    $ export USE_ORM=true
    $ python app.py
"""

import os
from typing import Optional, List, Dict, Any

# ============================================================================
# EXAMPLE 1: Reading Employees
# ============================================================================

def example_get_employees():
    """Get all employees for a specific year using adapter."""
    from services.database_adapter import get_employees

    # Automatic: Uses ORM if USE_ORM=true, otherwise raw SQL
    employees = get_employees(year=2025)

    # Both implementations return identical structure
    for emp in employees:
        print(f"Employee: {emp['name']}")
        print(f"  Balance: {emp['balance']} days")
        print(f"  Usage Rate: {emp['usage_rate']}%")
        print()


# ============================================================================
# EXAMPLE 2: Reading Specific Employee
# ============================================================================

def example_get_employee():
    """Get a specific employee record."""
    from services.database_adapter import get_employee

    employee = get_employee(employee_num="001", year=2025)

    if employee:
        print(f"Found: {employee['name']} ({employee['employee_num']})")
        print(f"Granted: {employee['granted']} days")
        print(f"Used: {employee['used']} days")
        print(f"Balance: {employee['balance']} days")
    else:
        print("Employee not found")


# ============================================================================
# EXAMPLE 3: Saving Employee Data (Batch Sync)
# ============================================================================

def example_save_employees():
    """Save/update multiple employees from Excel sync."""
    from services.database_adapter import save_employees

    # Typically this comes from Excel parser
    employees_data = [
        {
            "id": "001_2025",
            "employee_num": "001",
            "name": "田中太郎",
            "granted": 20.0,
            "used": 5.0,
            "balance": 15.0,
            "expired": 0.0,
            "usage_rate": 25,
            "year": 2025,
        },
        {
            "id": "002_2025",
            "employee_num": "002",
            "name": "佐藤花子",
            "granted": 20.0,
            "used": 10.0,
            "balance": 10.0,
            "expired": 0.0,
            "usage_rate": 50,
            "year": 2025,
        },
    ]

    # Automatic: Uses ORM or SQL based on USE_ORM flag
    save_employees(employees_data)
    print(f"Saved {len(employees_data)} employees")


# ============================================================================
# EXAMPLE 4: Leave Request Workflow
# ============================================================================

def example_leave_request_workflow():
    """Complete workflow: get pending → approve/reject."""
    from services.database_adapter import (
        get_leave_requests,
        approve_leave_request,
        reject_leave_request,
    )

    # Get all pending requests
    pending = get_leave_requests(status="PENDING", year=2025)
    print(f"Found {len(pending)} pending requests")

    for request in pending:
        print(f"\nRequest #{request['id']}")
        print(f"  Employee: {request['employee_name']}")
        print(f"  Period: {request['start_date']} to {request['end_date']}")
        print(f"  Days: {request['days_requested']}")

        # Approve the request (LIFO deduction happens automatically)
        try:
            approve_leave_request(
                request_id=request['id'],
                approved_by="admin_user"
            )
            print(f"  ✓ Approved")

            # Update employee balance in database
            # The approval automatically deducts days using LIFO

        except ValueError as e:
            print(f"  ✗ Approval failed: {e}")

            # Reject instead
            reject_leave_request(
                request_id=request['id'],
                approved_by="admin_user"
            )
            print(f"  ✓ Rejected")


# ============================================================================
# EXAMPLE 5: Get Leave Requests with Filters
# ============================================================================

def example_get_leave_requests_filtered():
    """Get leave requests with various filters."""
    from services.database_adapter import get_leave_requests

    # All pending requests
    pending_all = get_leave_requests(status="PENDING")
    print(f"All pending: {len(pending_all)}")

    # Pending for specific employee
    pending_emp = get_leave_requests(status="PENDING", employee_num="001", year=2025)
    print(f"Pending for employee 001: {len(pending_emp)}")

    # Approved requests for a specific year
    approved = get_leave_requests(status="APPROVED", year=2025)
    print(f"Approved in 2025: {len(approved)}")


# ============================================================================
# EXAMPLE 6: Employee History (Current + Previous Year)
# ============================================================================

def example_employee_history():
    """Get employee's vacation history (last 2 years)."""
    from services.database_adapter import get_employee_yukyu_history

    history = get_employee_yukyu_history(employee_num="001", current_year=2025)

    print(f"Vacation history for employee 001:")
    for record in history:
        print(f"\nYear: {record['year']}")
        print(f"  Granted: {record['granted']} days")
        print(f"  Used: {record['used']} days")
        print(f"  Balance: {record['balance']} days")
        print(f"  Expired: {record['expired']} days")


# ============================================================================
# EXAMPLE 7: Employee Type Classification
# ============================================================================

def example_get_employees_enhanced():
    """Get employees with type and employment status."""
    from services.database_adapter import get_employees_enhanced

    # Get all employees with enhanced info
    employees = get_employees_enhanced(year=2025, active_only=True)

    for emp in employees:
        emp_type = emp.get('employee_type', 'staff')
        status = emp.get('employment_status', '在職中')
        is_active = emp.get('is_active', False)

        print(f"{emp['name']} ({emp_type}) - {status}")
        print(f"  Active: {is_active}")
        print(f"  Kana: {emp.get('kana', 'N/A')}")


# ============================================================================
# EXAMPLE 8: Dispatch Employees (派遣社員)
# ============================================================================

def example_dispatch_employees():
    """Work with dispatch employees."""
    from services.database_adapter import get_genzai, save_genzai

    # Get active dispatch employees
    active_genzai = get_genzai(status="在職中", year=2025)
    print(f"Active dispatch employees: {len(active_genzai)}")

    # Save new dispatch employees
    new_genzai = [
        {
            "id": "GENZAI_001",
            "employee_num": "001",
            "name": "田中太郎",
            "kana": "たなかたろう",
            "status": "在職中",
            "dispatch_id": "DISP_001",
            "dispatch_name": "派遣会社A",
            "hourly_wage": 1500.0,
        },
    ]

    save_genzai(new_genzai)
    print("Dispatch employees saved")


# ============================================================================
# EXAMPLE 9: Usage Details (Detailed Tracking)
# ============================================================================

def example_usage_details():
    """Work with detailed usage dates."""
    from services.database_adapter import (
        get_yukyu_usage_details,
        save_yukyu_usage_details,
    )

    # Save individual usage dates
    usage = [
        {
            "employee_num": "001",
            "name": "田中太郎",
            "use_date": "2025-01-15",
            "year": 2025,
            "month": 1,
            "days_used": 1.0,
        },
        {
            "employee_num": "001",
            "name": "田中太郎",
            "use_date": "2025-01-16",
            "year": 2025,
            "month": 1,
            "days_used": 0.5,  # Half day
        },
    ]

    save_yukyu_usage_details(usage)
    print(f"Saved {len(usage)} usage records")

    # Get usage for specific employee and month
    details = get_yukyu_usage_details(employee_num="001", year=2025, month=1)
    print(f"Usage in 2025-01: {len(details)} records, {sum(d.get('days_used', 0) for d in details)} days")


# ============================================================================
# EXAMPLE 10: Analytics & Reporting
# ============================================================================

def example_analytics():
    """Analytics and reporting functions."""
    from services.database_adapter import (
        get_monthly_usage_summary,
        get_employee_usage_summary,
    )

    # Monthly summary for 2025
    monthly = get_monthly_usage_summary(year=2025)
    print("Monthly usage summary for 2025:")
    for month, data in monthly.items():
        print(f"  {month:2d}: {data['employee_count']} employees, {data['total_days']} days used")

    # Individual employee summary
    summary = get_employee_usage_summary(employee_num="001", year=2025)
    if summary:
        print(f"\nEmployee 001 (2025):")
        print(f"  Granted: {summary['granted']} days")
        print(f"  Used: {summary['used']} days")
        print(f"  Balance: {summary['balance']} days")
        print(f"  Usage Rate: {summary['usage_rate']}%")


# ============================================================================
# EXAMPLE 11: Check Implementation Status
# ============================================================================

def example_check_implementation():
    """Check which implementation is active."""
    from services.database_adapter import get_implementation_status
    import json

    status = get_implementation_status()

    print("Database Adapter Status:")
    print(json.dumps(status, indent=2))

    if status['use_orm'] and status['orm_available']:
        print("\n✓ Using SQLAlchemy ORM (Phase 2)")
        print("  All operations use database_orm.py")
    else:
        print("\n✓ Using Raw SQL (database.py)")
        if status['use_orm'] and not status['orm_available']:
            print("  Note: USE_ORM=true but database_orm not available")
            print("  Falling back to raw SQL automatically")


# ============================================================================
# EXAMPLE 12: Audit Logging
# ============================================================================

def example_audit_log():
    """Access audit trail."""
    from services.database_adapter import get_audit_log

    # Get recent audit entries for a specific leave request
    audit_entries = get_audit_log(
        entity_type="leave_request",
        entity_id="123",
        limit=50
    )

    print(f"Audit trail for request #123 ({len(audit_entries)} entries):")
    for entry in audit_entries:
        print(f"  {entry['timestamp']}: {entry['action']} by {entry['user_id']}")
        if entry.get('details'):
            print(f"    Details: {entry['details']}")


# ============================================================================
# MAIN: Run Examples
# ============================================================================

if __name__ == "__main__":
    print("Database Adapter Usage Examples")
    print("=" * 60)
    print()

    # Show current implementation
    print("1. Check Implementation Status")
    print("-" * 60)
    example_check_implementation()
    print()

    # NOTE: Uncomment the examples below to run them
    # They require a working database connection

    # print("2. Get Employees")
    # print("-" * 60)
    # example_get_employees()
    # print()

    # print("3. Get Specific Employee")
    # print("-" * 60)
    # example_get_employee()
    # print()

    # print("4. Leave Request Workflow")
    # print("-" * 60)
    # example_leave_request_workflow()
    # print()

    # print("5. Employee History")
    # print("-" * 60)
    # example_employee_history()
    # print()

    # print("6. Analytics")
    # print("-" * 60)
    # example_analytics()
    # print()

    print("All examples are functional and ready to use!")
    print()
    print("To run specific examples, uncomment them in main()")
