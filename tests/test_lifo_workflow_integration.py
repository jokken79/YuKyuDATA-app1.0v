"""
Integration Test: LIFO Workflow
Tests the complete leave request approval workflow with LIFO deduction
"""

import pytest
from datetime import datetime, timezone
from orm import SessionLocal
from orm.models.employee import Employee
from orm.models.leave_request import LeaveRequest
from database import create_leave_request, approve_leave_request
from sqlalchemy import and_
import uuid


@pytest.fixture
def setup_employee():
    """Setup test employee with vacation balance"""
    emp_num = f"INTEG_{uuid.uuid4().hex[:8]}"

    with SessionLocal() as session:
        emp = Employee(
            employee_num=emp_num,
            year=2025,
            name="Integration Test Employee",
            granted=20,
            used=0,
            balance=20,
            grant_date="2025-04-21",
            status="在職中"
        )
        session.add(emp)
        session.commit()

    return emp_num


def test_basic_approval_workflow(setup_employee):
    """Test basic leave request approval with LIFO deduction"""
    emp_num = setup_employee

    # Create leave request
    with SessionLocal() as session:
        req = LeaveRequest(
            employee_num=emp_num,
            employee_name="Integration Test",
            start_date="2025-05-01",
            end_date="2025-05-05",
            days_requested=3,
            leave_type="full",
            reason="Integration test",
            status="PENDING",
            year=2025
        )
        session.add(req)
        session.commit()
        req_id = str(req.id)

    # Approve leave request
    result = approve_leave_request(req_id, "test_admin")
    assert result is True

    # Verify employee balance was deducted
    with SessionLocal() as session:
        emp = session.query(Employee).filter(
            Employee.employee_num == emp_num
        ).first()

        assert emp.used == 3, f"Expected 3 days used, got {emp.used}"
        assert emp.balance == 17, f"Expected 17 days balance, got {emp.balance}"

    # Verify leave request is approved
    with SessionLocal() as session:
        req = session.query(LeaveRequest).filter(
            LeaveRequest.id == req_id
        ).first()

        assert req.status == "APPROVED"
        assert req.approver == "test_admin"
        assert req.approved_at is not None


def test_approval_with_insufficient_balance(setup_employee):
    """Test that approval fails with insufficient balance"""
    emp_num = setup_employee

    # Create leave request for more days than available
    with SessionLocal() as session:
        req = LeaveRequest(
            employee_num=emp_num,
            employee_name="Integration Test",
            start_date="2025-05-01",
            end_date="2025-05-25",
            days_requested=25,  # Only 20 available
            leave_type="full",
            reason="More than available",
            status="PENDING",
            year=2025
        )
        session.add(req)
        session.commit()
        req_id = str(req.id)

    # Try to approve (should fail)
    with pytest.raises(ValueError, match="Insufficient vacation balance"):
        approve_leave_request(req_id, "test_admin")

    # Verify balance unchanged
    with SessionLocal() as session:
        emp = session.query(Employee).filter(
            Employee.employee_num == emp_num
        ).first()

        assert emp.used == 0, "Balance should not change on failed approval"
        assert emp.balance == 20, "Balance should remain 20"

    # Verify leave request still PENDING
    with SessionLocal() as session:
        req = session.query(LeaveRequest).filter(
            LeaveRequest.id == req_id
        ).first()

        assert req.status == "PENDING", "Request should still be PENDING"


def test_multiple_sequential_approvals(setup_employee):
    """Test multiple sequential leave requests"""
    emp_num = setup_employee

    # Create and approve 3 requests
    request_ids = []
    for i, days in enumerate([5, 7, 4]):
        with SessionLocal() as session:
            req = LeaveRequest(
                employee_num=emp_num,
                employee_name="Integration Test",
                start_date=f"2025-05-{(i*10)+1:02d}",
                end_date=f"2025-05-{(i*10)+days:02d}",
                days_requested=days,
                leave_type="full",
                reason=f"Request {i+1}",
                status="PENDING",
                year=2025
            )
            session.add(req)
            session.commit()
            request_ids.append(str(req.id))

    # Approve first two (5 + 7 = 12 days, leaving 8)
    for req_id in request_ids[:2]:
        result = approve_leave_request(req_id, "test_admin")
        assert result is True

    # Third should succeed (4 days < 8 remaining)
    result = approve_leave_request(request_ids[2], "test_admin")
    assert result is True

    # Verify final balance
    with SessionLocal() as session:
        emp = session.query(Employee).filter(
            Employee.employee_num == emp_num
        ).first()

        expected_used = 5 + 7 + 4  # 16 days
        assert emp.used == expected_used, f"Expected {expected_used} days used"
        assert emp.balance == 4, f"Expected 4 days balance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
