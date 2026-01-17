"""
Unit Tests for Phase 1: ORM Read Operations Migration
=====================================================

Tests all ORM read operations to ensure they match the original raw SQL
implementations in terms of:
- Data returned (same fields, same values)
- Data types (dict, list of dict, or scalar)
- Filtering behavior
- Sorting/ordering
- Null/None handling

Total Tests: 25 for Phase 1 Read Operations
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from orm import Base
from orm.models import (
    Employee,
    LeaveRequest,
    YukyuUsageDetail,
    GenzaiEmployee,
    UkeoiEmployee,
    Notification,
    NotificationRead,
    AuditLog,
    User,
)
import database_orm

# Create an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all ORM tables in test database before running tests."""
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def test_session():
    """Create a fresh test database session for each test."""
    db = TestSessionLocal()
    yield db
    db.rollback()
    db.close()


@pytest.fixture
def monkeypatch_orm(test_session):
    """Monkeypatch database_orm to use test database."""
    with patch('database_orm.SessionLocal', TestSessionLocal):
        yield test_session


@pytest.fixture(autouse=True)
def cleanup(test_session):
    """Clean up all tables before each test."""
    # Delete in order of dependencies
    test_session.query(NotificationRead).delete()
    test_session.query(Notification).delete()
    test_session.query(LeaveRequest).delete()
    test_session.query(YukyuUsageDetail).delete()
    test_session.query(GenzaiEmployee).delete()
    test_session.query(UkeoiEmployee).delete()
    test_session.query(Employee).delete()
    test_session.query(AuditLog).delete()
    test_session.query(User).delete()
    test_session.commit()


# ============================================
# Subtask 1.1: Basic Employee Reads (10 tests)
# ============================================

def test_get_employees_orm_all(test_session, monkeypatch_orm):
    """Test getting all employees without year filter."""
    # Setup
    emp1 = Employee(employee_num="001", year=2025, name="Taro", granted=10.0, used=2.0, balance=8.0)
    emp2 = Employee(employee_num="002", year=2025, name="Hanako", granted=11.0, used=0.0, balance=11.0)
    emp3 = Employee(employee_num="001", year=2024, name="Taro", granted=10.0, used=8.0, balance=2.0)
    test_session.add_all([emp1, emp2, emp3])
    test_session.commit()

    # Execute
    results = database_orm.get_employees_orm()

    # Verify
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results)
    assert results[0]['employee_num'] in ['001', '002']


def test_get_employees_orm_by_year(test_session, monkeypatch_orm):
    """Test getting employees filtered by year."""
    # Setup
    emp1 = Employee(employee_num="001", year=2025, name="Taro", granted=10.0)
    emp2 = Employee(employee_num="002", year=2025, name="Hanako", granted=11.0)
    emp3 = Employee(employee_num="001", year=2024, name="Taro", granted=10.0)
    test_session.add_all([emp1, emp2, emp3])
    test_session.commit()

    # Execute
    results = database_orm.get_employees_orm(year=2025)

    # Verify
    assert len(results) == 2
    assert all(r['year'] == 2025 for r in results)


def test_get_employee_orm_single(test_session, monkeypatch_orm):
    """Test getting a single employee by number and year."""
    # Setup
    emp = Employee(employee_num="001", year=2025, name="Taro", granted=10.0, balance=10.0)
    test_session.add(emp)
    test_session.commit()

    # Execute
    result = database_orm.get_employee_orm("001", 2025)

    # Verify
    assert result is not None
    assert result['employee_num'] == "001"
    assert result['year'] == 2025
    assert result['name'] == "Taro"
    assert result['balance'] == 10.0


def test_get_employee_orm_not_found(test_session, monkeypatch_orm):
    """Test getting non-existent employee returns None."""
    # Execute
    result = database_orm.get_employee_orm("999", 2025)

    # Verify
    assert result is None


def test_get_available_years_orm(test_session, monkeypatch_orm):
    """Test getting distinct years."""
    # Setup
    emp1 = Employee(employee_num="001", year=2023, name="Taro", granted=10.0)
    emp2 = Employee(employee_num="001", year=2024, name="Taro", granted=10.0)
    emp3 = Employee(employee_num="001", year=2025, name="Taro", granted=10.0)
    emp4 = Employee(employee_num="002", year=2025, name="Hanako", granted=11.0)
    test_session.add_all([emp1, emp2, emp3, emp4])
    test_session.commit()

    # Execute
    years = database_orm.get_available_years_orm()

    # Verify
    assert len(years) == 3
    assert set(years) == {2023, 2024, 2025}
    assert years == [2025, 2024, 2023]  # Descending order


def test_get_employees_enhanced_orm(test_session, monkeypatch_orm):
    """Test getting employees with type and status information."""
    # Setup
    emp = Employee(employee_num="001", year=2025, name="Taro", granted=10.0, usage_rate=20.0)
    genzai = GenzaiEmployee(employee_num="001", status="在職中", name="Taro")
    test_session.add_all([emp, genzai])
    test_session.commit()

    # Execute
    results = database_orm.get_employees_enhanced_orm(year=2025)

    # Verify
    assert len(results) == 1
    assert results[0]['employee_type'] == 'genzai'
    assert results[0]['employment_status'] == '在職中'
    assert results[0]['is_active'] == 1


def test_get_employees_enhanced_orm_staff(test_session, monkeypatch_orm):
    """Test that employees without genzai/ukeoi are marked as staff."""
    # Setup
    emp = Employee(employee_num="003", year=2025, name="Admin", granted=10.0, usage_rate=0.0)
    test_session.add(emp)
    test_session.commit()

    # Execute
    results = database_orm.get_employees_enhanced_orm(year=2025)

    # Verify
    assert len(results) == 1
    assert results[0]['employee_type'] == 'staff'
    assert results[0]['is_active'] == 1


def test_get_employees_enhanced_orm_active_only(test_session, monkeypatch_orm):
    """Test filtering by active status."""
    # Setup
    emp_active = Employee(employee_num="001", year=2025, name="Taro", granted=10.0, usage_rate=20.0)
    emp_inactive = Employee(employee_num="002", year=2025, name="Hanako", granted=10.0, usage_rate=0.0)
    genzai_active = GenzaiEmployee(employee_num="001", status="在職中", name="Taro")
    genzai_inactive = GenzaiEmployee(employee_num="002", status="退職", name="Hanako")
    test_session.add_all([emp_active, emp_inactive, genzai_active, genzai_inactive])
    test_session.commit()

    # Execute
    results = database_orm.get_employees_enhanced_orm(year=2025, active_only=True)

    # Verify
    assert len(results) == 1
    assert results[0]['employee_num'] == "001"
    assert results[0]['is_active'] == 1


def test_get_employees_enhanced_orm_sorting(test_session, monkeypatch_orm):
    """Test that results are sorted by usage_rate descending."""
    # Setup
    emp1 = Employee(employee_num="001", year=2025, name="Taro", granted=10.0, usage_rate=50.0)
    emp2 = Employee(employee_num="002", year=2025, name="Hanako", granted=10.0, usage_rate=20.0)
    emp3 = Employee(employee_num="003", year=2025, name="Admin", granted=10.0, usage_rate=100.0)
    test_session.add_all([emp1, emp2, emp3])
    test_session.commit()

    # Execute
    results = database_orm.get_employees_enhanced_orm(year=2025)

    # Verify
    assert len(results) == 3
    assert results[0]['usage_rate'] == 100.0
    assert results[1]['usage_rate'] == 50.0
    assert results[2]['usage_rate'] == 20.0


# ============================================
# Subtask 1.2: Leave Request Reads (8 tests)
# ============================================

def test_get_leave_requests_orm_all(session):
    """Test getting all leave requests."""
    # Setup
    req1 = LeaveRequest(
        employee_num="001",
        start_date="2025-01-01",
        end_date="2025-01-05",
        days_requested=5.0,
        year=2025,
        status="PENDING"
    )
    req2 = LeaveRequest(
        employee_num="002",
        start_date="2025-02-01",
        end_date="2025-02-02",
        days_requested=2.0,
        year=2025,
        status="APPROVED"
    )
    session.add_all([req1, req2])
    session.commit()

    # Execute
    results = database_orm.get_leave_requests_orm()

    # Verify
    assert len(results) == 2
    assert all(isinstance(r, dict) for r in results)


def test_get_leave_requests_orm_by_status(session):
    """Test filtering leave requests by status."""
    # Setup
    req1 = LeaveRequest(
        employee_num="001",
        start_date="2025-01-01",
        end_date="2025-01-05",
        days_requested=5.0,
        year=2025,
        status="PENDING"
    )
    req2 = LeaveRequest(
        employee_num="002",
        start_date="2025-02-01",
        end_date="2025-02-02",
        days_requested=2.0,
        year=2025,
        status="APPROVED"
    )
    session.add_all([req1, req2])
    session.commit()

    # Execute
    results = database_orm.get_leave_requests_orm(status="PENDING")

    # Verify
    assert len(results) == 1
    assert results[0]['status'] == "PENDING"


def test_get_leave_requests_orm_by_employee(session):
    """Test filtering by employee number."""
    # Setup
    req1 = LeaveRequest(
        employee_num="001",
        start_date="2025-01-01",
        end_date="2025-01-05",
        days_requested=5.0,
        year=2025
    )
    req2 = LeaveRequest(
        employee_num="001",
        start_date="2025-02-01",
        end_date="2025-02-02",
        days_requested=2.0,
        year=2025
    )
    req3 = LeaveRequest(
        employee_num="002",
        start_date="2025-03-01",
        end_date="2025-03-05",
        days_requested=5.0,
        year=2025
    )
    session.add_all([req1, req2, req3])
    session.commit()

    # Execute
    results = database_orm.get_leave_requests_orm(employee_num="001")

    # Verify
    assert len(results) == 2
    assert all(r['employee_num'] == "001" for r in results)


def test_get_leave_request_orm_single(session):
    """Test getting a single leave request by ID."""
    # Setup
    req = LeaveRequest(
        employee_num="001",
        start_date="2025-01-01",
        end_date="2025-01-05",
        days_requested=5.0,
        year=2025,
        status="PENDING"
    )
    session.add(req)
    session.commit()

    # Execute
    result = database_orm.get_leave_request_orm(req.id)

    # Verify
    assert result is not None
    assert result['id'] == req.id
    assert result['employee_num'] == "001"


def test_get_employee_yukyu_history_orm(session):
    """Test getting leave history for an employee."""
    # Setup
    req1 = LeaveRequest(
        employee_num="001",
        start_date="2025-01-01",
        end_date="2025-01-05",
        days_requested=5.0,
        year=2025
    )
    req2 = LeaveRequest(
        employee_num="001",
        start_date="2025-02-01",
        end_date="2025-02-02",
        days_requested=2.0,
        year=2025
    )
    session.add_all([req1, req2])
    session.commit()

    # Execute
    results = database_orm.get_employee_yukyu_history_orm("001")

    # Verify
    assert len(results) == 2
    assert all(r['employee_num'] == "001" for r in results)
    # Should be ordered by created_at desc (most recent first)
    assert results[0]['created_at'] >= results[1]['created_at']


def test_get_pending_approvals_orm(session):
    """Test getting pending leave requests."""
    # Setup
    req1 = LeaveRequest(
        employee_num="001",
        start_date="2025-01-01",
        end_date="2025-01-05",
        days_requested=5.0,
        year=2025,
        status="PENDING"
    )
    req2 = LeaveRequest(
        employee_num="002",
        start_date="2025-02-01",
        end_date="2025-02-02",
        days_requested=2.0,
        year=2025,
        status="APPROVED"
    )
    req3 = LeaveRequest(
        employee_num="003",
        start_date="2025-03-01",
        end_date="2025-03-05",
        days_requested=5.0,
        year=2025,
        status="PENDING"
    )
    session.add_all([req1, req2, req3])
    session.commit()

    # Execute
    results = database_orm.get_pending_approvals_orm()

    # Verify
    assert len(results) == 2
    assert all(r['status'] == "PENDING" for r in results)


# ============================================
# Subtask 1.3: Yukyu Usage Detail Reads (6 tests)
# ============================================

def test_get_yukyu_usage_details_orm_all(session):
    """Test getting all yukyu usage details."""
    # Setup
    detail1 = YukyuUsageDetail(employee_num="001", use_date="2025-01-10", days_used=1.0)
    detail2 = YukyuUsageDetail(employee_num="001", use_date="2025-01-15", days_used=0.5)
    detail3 = YukyuUsageDetail(employee_num="002", use_date="2025-02-01", days_used=1.0)
    session.add_all([detail1, detail2, detail3])
    session.commit()

    # Execute
    results = database_orm.get_yukyu_usage_details_orm()

    # Verify
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results)


def test_get_yukyu_usage_details_orm_by_employee(session):
    """Test filtering usage details by employee."""
    # Setup
    detail1 = YukyuUsageDetail(employee_num="001", use_date="2025-01-10", days_used=1.0)
    detail2 = YukyuUsageDetail(employee_num="001", use_date="2025-01-15", days_used=0.5)
    detail3 = YukyuUsageDetail(employee_num="002", use_date="2025-02-01", days_used=1.0)
    session.add_all([detail1, detail2, detail3])
    session.commit()

    # Execute
    results = database_orm.get_yukyu_usage_details_orm(employee_num="001")

    # Verify
    assert len(results) == 2
    assert all(r['employee_num'] == "001" for r in results)


def test_get_yukyu_usage_details_orm_by_year(session):
    """Test filtering usage details by year."""
    # Setup
    detail1 = YukyuUsageDetail(employee_num="001", use_date="2025-01-10", days_used=1.0)
    detail2 = YukyuUsageDetail(employee_num="001", use_date="2025-02-15", days_used=0.5)
    detail3 = YukyuUsageDetail(employee_num="002", use_date="2024-12-01", days_used=1.0)
    session.add_all([detail1, detail2, detail3])
    session.commit()

    # Execute
    results = database_orm.get_yukyu_usage_details_orm(year=2025)

    # Verify
    assert len(results) == 2
    assert all("2025" in r['use_date'] for r in results)


def test_get_yukyu_usage_details_orm_by_month(session):
    """Test filtering usage details by year and month."""
    # Setup
    detail1 = YukyuUsageDetail(employee_num="001", use_date="2025-01-10", days_used=1.0)
    detail2 = YukyuUsageDetail(employee_num="001", use_date="2025-02-15", days_used=0.5)
    detail3 = YukyuUsageDetail(employee_num="002", use_date="2025-01-20", days_used=1.0)
    session.add_all([detail1, detail2, detail3])
    session.commit()

    # Execute
    results = database_orm.get_yukyu_usage_details_orm(year=2025, month=1)

    # Verify
    assert len(results) == 2
    assert all("2025-01" in r['use_date'] for r in results)


def test_get_yukyu_usage_detail_orm_single(session):
    """Test getting a single usage detail by ID."""
    # Setup
    detail = YukyuUsageDetail(employee_num="001", use_date="2025-01-10", days_used=1.0)
    session.add(detail)
    session.commit()

    # Execute
    result = database_orm.get_yukyu_usage_detail_orm(detail.id)

    # Verify
    assert result is not None
    assert result['employee_num'] == "001"
    assert result['days_used'] == 1.0


def test_get_yukyu_usage_detail_orm_not_found(session):
    """Test that non-existent detail returns None."""
    # Execute
    result = database_orm.get_yukyu_usage_detail_orm(9999)

    # Verify
    assert result is None


# ============================================
# SUMMARY AND HELPER ASSERTIONS
# ============================================

class TestHelper:
    """Helper assertions for test verification."""

    @staticmethod
    def assert_dict_response(response):
        """Assert response is a dict."""
        assert isinstance(response, dict)

    @staticmethod
    def assert_list_response(response):
        """Assert response is a list of dicts."""
        assert isinstance(response, list)
        for item in response:
            assert isinstance(item, dict)

    @staticmethod
    def assert_scalar_response(response):
        """Assert response is a scalar (int, float, str)."""
        assert isinstance(response, (int, float, str))


@pytest.mark.parametrize("year,expected_count", [
    (2025, 2),
    (2024, 1),
    (2023, 0),
])
def test_get_employees_orm_parametrized(session, year, expected_count):
    """Test get_employees with multiple year parameters."""
    # Setup
    emp1 = Employee(employee_num="001", year=2025, name="Taro", granted=10.0)
    emp2 = Employee(employee_num="002", year=2025, name="Hanako", granted=11.0)
    emp3 = Employee(employee_num="001", year=2024, name="Taro", granted=10.0)
    session.add_all([emp1, emp2, emp3])
    session.commit()

    # Execute
    results = database_orm.get_employees_orm(year=year)

    # Verify
    assert len(results) == expected_count
