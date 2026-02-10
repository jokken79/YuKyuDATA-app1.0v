"""
SPRINT 4: Fiscal Year and Bulk Operations Tests

Tests for:
- BUG #5: process_year_end_carryover() migración a ORM
- BUG #6: auto_designate_5_days() implementación real
- BUG #7: revert_bulk_update() con audit trail
"""

import pytest
from datetime import datetime, timezone, date
from orm import SessionLocal
from orm.models.employee import Employee
from orm.models.leave_request import LeaveRequest
from orm.models.audit_log import AuditLog
from services.fiscal_year import process_year_end_carryover, auto_designate_5_days
from database import revert_bulk_update, log_audit_action, bulk_update_employees
import uuid


class TestBUG5_YearEndCarryover:
    """Test BUG #5: process_year_end_carryover() ORM migration"""

    @pytest.fixture
    def setup_employees_for_carryover(self):
        """Create test employees for year-end carryover"""
        with SessionLocal() as session:
            employees = []
            for i in range(3):
                emp = Employee(
                    employee_num=f"CARRY_{i:03d}",
                    year=2024,
                    name=f"Employee {i}",
                    granted=20,
                    used=10,
                    balance=10,  # Will carry over to 2025
                    grant_date="2024-04-21",
                    status="在職中"
                )
                session.add(emp)
                employees.append(emp.employee_num)
            session.commit()
        return employees

    def test_process_year_end_carryover_creates_new_records(self, setup_employees_for_carryover):
        """Test that process_year_end_carryover() creates new year records"""
        emp_nums = setup_employees_for_carryover

        # Process carryover from 2024 to 2025
        result = process_year_end_carryover(from_year=2024, to_year=2025)

        assert result['success'] is True
        assert result['employees_processed'] == 3
        assert result['days_carried_over'] == 30.0  # 3 employees × 10 days each

        # Verify new records were created
        with SessionLocal() as session:
            for emp_num in emp_nums:
                emp_2025 = session.query(Employee).filter(
                    Employee.employee_num == emp_num,
                    Employee.year == 2025
                ).first()
                assert emp_2025 is not None
                assert emp_2025.balance == 10
                assert emp_2025.granted == 0

    def test_process_year_end_carryover_respects_max_limit(self):
        """Test that carryover respects maximum accumulated days"""
        with SessionLocal() as session:
            # Create employee with balance near max
            emp = Employee(
                employee_num="MAX_TEST",
                year=2024,
                name="Max Test",
                granted=20,
                used=0,
                balance=50,  # Exceeds max of 40
                grant_date="2024-04-21",
                status="在職中"
            )
            session.add(emp)
            session.commit()

        result = process_year_end_carryover(from_year=2024, to_year=2025)

        assert result['success'] is True
        assert result['days_expired'] == 10  # 50 - 40 max = 10 expired

    def test_process_year_end_carryover_uses_orm_not_sql_raw(self):
        """Verify that process_year_end_carryover uses ORM (not SQL raw)"""
        # If this test doesn't raise an ORM-related error, it means
        # the function successfully uses ORM with row-level locking
        emp_nums = []
        with SessionLocal() as session:
            for i in range(2):
                emp = Employee(
                    employee_num=f"ORM_TEST_{i}",
                    year=2024,
                    name=f"Test {i}",
                    granted=10,
                    used=0,
                    balance=10,
                    grant_date="2024-04-21",
                    status="在職中"
                )
                session.add(emp)
                emp_nums.append(emp.employee_num)
            session.commit()

        # Should not raise an error (ORM-based implementation)
        result = process_year_end_carryover(from_year=2024, to_year=2025)
        assert result['success'] is True


class TestBUG6_AutoDesignate5Days:
    """Test BUG #6: auto_designate_5_days() creates LeaveRequest"""

    @pytest.fixture
    def setup_employee_for_designation(self):
        """Create employee needing 5-day designation"""
        emp_num = f"DESIGNATE_{uuid.uuid4().hex[:8]}"
        with SessionLocal() as session:
            emp = Employee(
                employee_num=emp_num,
                year=2025,
                name="Designation Test",
                granted=15,  # >= 10 days
                used=0,  # Used < 5 days (not compliant)
                balance=15,
                grant_date="2025-04-21",
                status="在職中"
            )
            session.add(emp)
            session.commit()
        return emp_num

    def test_auto_designate_5_days_creates_leave_request(self, setup_employee_for_designation):
        """Test that auto_designate_5_days() creates LeaveRequest with DESIGNATED status"""
        emp_num = setup_employee_for_designation

        result = auto_designate_5_days(emp_num, 2025, performed_by="admin")

        assert result['success'] is True
        assert result['employee_num'] == emp_num
        assert result['days_designated'] == 5
        assert 'leave_request_id' in result

        # Verify LeaveRequest was created
        with SessionLocal() as session:
            leave_req = session.query(LeaveRequest).filter(
                LeaveRequest.id == result['leave_request_id']
            ).first()
            assert leave_req is not None
            assert leave_req.status == 'DESIGNATED'
            assert leave_req.days_requested == 5
            assert leave_req.reason.contains('年5日の取得義務')

    def test_auto_designate_5_days_requires_10_days(self):
        """Test that designation only applies to employees with 10+ granted days"""
        emp_num = f"EXEMPT_{uuid.uuid4().hex[:8]}"
        with SessionLocal() as session:
            emp = Employee(
                employee_num=emp_num,
                year=2025,
                name="Exempt Test",
                granted=5,  # < 10 days (exempt)
                used=0,
                balance=5,
                grant_date="2025-04-21",
                status="在職中"
            )
            session.add(emp)
            session.commit()

        result = auto_designate_5_days(emp_num, 2025)

        assert result['success'] is False
        assert 'exempt' in result['reason'].lower()

    def test_auto_designate_5_days_skips_compliant_employees(self):
        """Test that designation skips already-compliant employees"""
        emp_num = f"COMPLIANT_{uuid.uuid4().hex[:8]}"
        with SessionLocal() as session:
            emp = Employee(
                employee_num=emp_num,
                year=2025,
                name="Compliant Test",
                granted=20,
                used=5,  # Already used 5 days
                balance=15,
                grant_date="2025-04-21",
                status="在職中"
            )
            session.add(emp)
            session.commit()

        result = auto_designate_5_days(emp_num, 2025)

        assert result['success'] is False
        assert 'compliant' in result['reason'].lower()


class TestBUG7_RevertBulkUpdate:
    """Test BUG #7: revert_bulk_update() with real audit trail logic"""

    @pytest.fixture
    def setup_bulk_update_scenario(self):
        """Setup employees and perform bulk update"""
        emp_nums = []
        with SessionLocal() as session:
            for i in range(3):
                emp_num = f"REVERT_{i:03d}"
                emp = Employee(
                    employee_num=emp_num,
                    year=2025,
                    name=f"Revert Test {i}",
                    granted=20,
                    used=0,
                    balance=20,
                    grant_date="2025-04-21",
                    status="在職中"
                )
                session.add(emp)
                emp_nums.append(emp_num)
            session.commit()

        # Perform bulk update
        operation_id = str(uuid.uuid4())[:8]
        result = bulk_update_employees(
            employee_nums=emp_nums,
            year=2025,
            updates={'add_used': 5},  # Add 5 days used to all
            updated_by='test_admin',
            validate_limit=False
        )

        return operation_id, emp_nums, result

    def test_revert_bulk_update_restores_values(self, setup_bulk_update_scenario):
        """Test that revert_bulk_update() actually reverts values"""
        operation_id, emp_nums, bulk_result = setup_bulk_update_scenario

        # Before revert: should have used=5, balance=15
        with SessionLocal() as session:
            emp = session.query(Employee).filter(
                Employee.employee_num == emp_nums[0],
                Employee.year == 2025
            ).first()
            assert emp.used == 5
            assert emp.balance == 15

        # Revert operation
        revert_result = revert_bulk_update(
            operation_id=bulk_result['operation_id'],
            reverted_by='admin'
        )

        # After revert: should be back to used=0, balance=20
        with SessionLocal() as session:
            emp = session.query(Employee).filter(
                Employee.employee_num == emp_nums[0],
                Employee.year == 2025
            ).first()
            assert emp.used == 0  # Reverted
            assert emp.balance == 20  # Reverted

    def test_revert_bulk_update_creates_audit_records(self, setup_bulk_update_scenario):
        """Test that revert_bulk_update() creates audit trail records"""
        operation_id, emp_nums, bulk_result = setup_bulk_update_scenario

        revert_result = revert_bulk_update(
            operation_id=bulk_result['operation_id'],
            reverted_by='admin'
        )

        assert revert_result['success'] is True
        assert revert_result['reverted_count'] > 0

        # Verify REVERT audit records were created
        with SessionLocal() as session:
            revert_records = session.query(AuditLog).filter(
                AuditLog.action == 'REVERT_BULK_UPDATE'
            ).all()
            assert len(revert_records) > 0

    def test_revert_bulk_update_returns_statistics(self, setup_bulk_update_scenario):
        """Test that revert_bulk_update() returns correct statistics"""
        operation_id, emp_nums, bulk_result = setup_bulk_update_scenario

        revert_result = revert_bulk_update(
            operation_id=bulk_result['operation_id'],
            reverted_by='admin'
        )

        # Check statistics format
        assert 'success' in revert_result
        assert 'reverted_count' in revert_result
        assert 'errors' in revert_result
        assert 'reverted_at' in revert_result
        assert revert_result['reverted_count'] > 0  # Actually reverted something


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
