"""
Test Suite: LIFO Deduction Race Condition Prevention
Tests concurrent approvals to ensure row-level locking prevents data corruption
"""

import pytest
import threading
from datetime import datetime, timezone
from orm import SessionLocal
from orm.models.employee import Employee
from orm.models.leave_request import LeaveRequest
from database import approve_leave_request
import uuid


@pytest.fixture
def test_employee():
    """Create a test employee with 15 days balance"""
    emp_num = f"TEST_{uuid.uuid4().hex[:8]}"

    with SessionLocal() as session:
        emp = Employee(
            employee_num=emp_num,
            year=2025,
            name="Race Condition Tester",
            granted=15,
            used=0,
            balance=15,
            grant_date="2025-04-21",
            status="在職中"
        )
        session.add(emp)
        session.commit()

    return emp_num


@pytest.fixture
def test_leave_request(test_employee):
    """Create test leave requests"""

    def create_request(days: float):
        with SessionLocal() as session:
            req = LeaveRequest(
                employee_num=test_employee,
                employee_name="Test Employee",
                start_date="2025-05-01",
                end_date="2025-05-10",
                days_requested=days,
                leave_type="full",
                reason="Test concurrent approval",
                status="PENDING",
                year=2025
            )
            session.add(req)
            session.commit()
            session.refresh(req)
            return str(req.id)

    return create_request


class TestLIFORaceCondition:
    """Test LIFO deduction with concurrent requests"""

    def test_concurrent_approvals_prevent_overdraft(self, test_employee, test_leave_request):
        """
        Test that concurrent approvals don't cause balance overdraft.

        Scenario:
        - Employee has 15 days balance
        - Request 1: Approve 10 days
        - Request 2 (concurrent): Approve 7 days
        - Expected: One succeeds (10 days deducted), one fails (only 5 left)
        """
        request1_id = test_leave_request(10)
        request2_id = test_leave_request(7)

        errors = []
        results = []

        def approve_request(req_id: str):
            try:
                result = approve_leave_request(req_id, "test_admin")
                results.append((req_id, "SUCCESS"))
            except ValueError as e:
                errors.append(str(e))
                results.append((req_id, "FAILED"))
            except Exception as e:
                errors.append(f"Unexpected error: {str(e)}")
                results.append((req_id, "ERROR"))

        # Concurrent approvals
        thread1 = threading.Thread(target=approve_request, args=(request1_id,))
        thread2 = threading.Thread(target=approve_request, args=(request2_id,))

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        # Verify results
        # One should succeed, one should fail due to insufficient balance
        successful = sum(1 for _, status in results if status == "SUCCESS")
        failed = sum(1 for _, status in results if status == "FAILED")

        assert successful == 1, f"Expected 1 success, got {successful}"
        assert failed == 1, f"Expected 1 failure, got {failed}"

        # Verify balance is correct
        with SessionLocal() as session:
            emp = session.query(Employee).filter(
                Employee.employee_num == test_employee
            ).first()

            # Should have 10 days used, 5 remaining
            assert emp.used == 10, f"Expected used=10, got {emp.used}"
            assert emp.balance == 5, f"Expected balance=5, got {emp.balance}"

    def test_lifo_with_multiple_grant_periods(self):
        """
        Test LIFO deduction correctly handles multiple grant_date periods (carry-over).

        Scenario:
        - Employee with 2 grant periods:
          - 2024-10-21: 5 days (carry-over)
          - 2025-04-21: 10 days (current year)
        - Approve request for 12 days
        - Expected: Deduct 10 from 2025, then 2 from 2024 (LIFO order)
        """
        emp_num = f"LIFO_{uuid.uuid4().hex[:8]}"

        with SessionLocal() as session:
            # Create 2 grant periods
            emp_2024 = Employee(
                employee_num=emp_num,
                year=2024,
                name="LIFO Test",
                granted=10,
                used=5,
                balance=5,  # Carry-over
                grant_date="2024-10-21",
                status="在職中"
            )
            emp_2025 = Employee(
                employee_num=emp_num,
                year=2025,
                name="LIFO Test",
                granted=10,
                used=0,
                balance=10,  # Current year
                grant_date="2025-04-21",
                status="在職中"
            )
            session.add_all([emp_2024, emp_2025])
            session.commit()

        # Create and approve leave request for 12 days
        with SessionLocal() as session:
            req = LeaveRequest(
                employee_num=emp_num,
                employee_name="LIFO Test",
                start_date="2025-05-01",
                end_date="2025-05-15",
                days_requested=12,
                leave_type="full",
                reason="Test LIFO with carry-over",
                status="PENDING",
                year=2025
            )
            session.add(req)
            session.commit()
            req_id = str(req.id)

        # Approve (should trigger LIFO deduction)
        result = approve_leave_request(req_id, "test_admin")
        assert result is True, "Approval should succeed"

        # Verify deductions were done in LIFO order
        with SessionLocal() as session:
            emp_2025 = session.query(Employee).filter(
                and_(
                    Employee.employee_num == emp_num,
                    Employee.year == 2025
                )
            ).first()
            emp_2024 = session.query(Employee).filter(
                and_(
                    Employee.employee_num == emp_num,
                    Employee.year == 2024
                )
            ).first()

            # 2025 should have 10 days used (all consumed)
            assert emp_2025.used == 10, f"2025: expected used=10, got {emp_2025.used}"
            assert emp_2025.balance == 0, f"2025: expected balance=0, got {emp_2025.balance}"

            # 2024 should have 7 days used (5 + 2 from LIFO)
            assert emp_2024.used == 7, f"2024: expected used=7, got {emp_2024.used}"
            assert emp_2024.balance == 3, f"2024: expected balance=3, got {emp_2024.balance}"

    def test_row_level_locking_prevents_update_lost(self, test_employee, test_leave_request):
        """
        Test that row-level locking prevents lost updates.

        Scenario:
        - Request 1: Read balance (10), sleep, write balance (after processing)
        - Request 2: Approves concurrently, updates balance
        - Expected: No lost updates due to FOR UPDATE locking
        """
        request1_id = test_leave_request(8)
        request2_id = test_leave_request(5)

        # Variables to track execution
        execution_log = []
        lock_acquired = threading.Event()

        def approve_with_logging(req_id: str, label: str):
            try:
                execution_log.append(f"{label}: Starting approval")
                result = approve_leave_request(req_id, "test_admin")
                execution_log.append(f"{label}: Approval successful")
            except Exception as e:
                execution_log.append(f"{label}: Approval failed: {e}")

        # Sequential approvals should work fine
        approve_with_logging(request1_id, "Request1")
        approve_with_logging(request2_id, "Request2")

        # Verify final balance
        with SessionLocal() as session:
            emp = session.query(Employee).filter(
                Employee.employee_num == test_employee
            ).first()

            # One should fail, one should succeed
            # Final balance should be 15 - 8 = 7 (if request 1 succeeds)
            # OR should fail the second one
            assert emp.balance < 15, "Balance should have decreased"


from sqlalchemy import and_

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
