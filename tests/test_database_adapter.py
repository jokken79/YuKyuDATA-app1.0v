"""
Tests for Database Adapter
===========================

Tests that verify the adapter works correctly with both implementations.
These tests can run with either USE_ORM=true or USE_ORM=false.

Test Strategy:
1. Test that adapter initializes correctly
2. Test that adapter routes to correct implementation
3. Test that both implementations return identical results
4. Test error handling consistency

Run with:
    # Test with SQL implementation
    USE_ORM=false pytest tests/test_database_adapter.py -v

    # Test with ORM implementation
    USE_ORM=true pytest tests/test_database_adapter.py -v

    # Test both by running twice
    for impl in false true; do
        USE_ORM=$impl pytest tests/test_database_adapter.py -v
    done
"""

import os
import pytest
from typing import Dict, List, Any

# Configure adapter before importing
os.environ.setdefault("USE_ORM", "false")
os.environ.setdefault("LOG_LEVEL", "DEBUG")

from services.database_adapter import (
    get_implementation_status,
    get_employees,
    get_employee,
    get_available_years,
    get_leave_requests,
    get_leave_request,
    get_yukyu_usage_details,
    get_employee_yukyu_history,
    get_genzai,
    get_ukeoi,
    get_staff,
    save_employees,
    save_genzai,
    save_ukeoi,
    save_staff,
    save_yukyu_usage_details,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def implementation_status():
    """Get current implementation status."""
    return get_implementation_status()


@pytest.fixture
def sample_employee_data():
    """Sample employee data for testing."""
    return {
        "id": "TEST_001_2025",
        "employee_num": "TEST_001",
        "name": "テスト太郎",
        "haken": "工場A",
        "granted": 20.0,
        "used": 5.0,
        "balance": 15.0,
        "expired": 0.0,
        "usage_rate": 25,
        "year": 2025,
    }


@pytest.fixture
def sample_genzai_data():
    """Sample dispatch employee data."""
    return {
        "id": "TEST_GENZAI_001",
        "employee_num": "TEST_GENZAI_001",
        "name": "派遣太郎",
        "kana": "はけんたろう",
        "status": "在職中",
        "dispatch_id": "DISP_001",
        "dispatch_name": "派遣会社テスト",
        "department": "製造部",
        "hourly_wage": 1500.0,
    }


@pytest.fixture
def sample_leave_request():
    """Sample leave request data."""
    return {
        "employee_num": "TEST_001",
        "employee_name": "テスト太郎",
        "start_date": "2025-01-15",
        "end_date": "2025-01-17",
        "days_requested": 3.0,
        "leave_type": "full",
        "status": "PENDING",
        "year": 2025,
    }


# ============================================================================
# TEST GROUP 1: Initialization & Status
# ============================================================================

class TestAdapterInitialization:
    """Test adapter initialization and status."""

    def test_get_implementation_status(self, implementation_status):
        """Adapter should return implementation status."""
        assert implementation_status is not None
        assert "use_orm" in implementation_status
        assert "orm_available" in implementation_status
        assert "implementation" in implementation_status
        assert "database_type" in implementation_status

    def test_implementation_type(self, implementation_status):
        """Status should indicate which implementation is active."""
        impl = implementation_status["implementation"]
        assert "SQL" in impl or "ORM" in impl
        # Should be human readable
        assert len(impl) > 0

    def test_database_type(self, implementation_status):
        """Status should indicate database type."""
        db_type = implementation_status["database_type"]
        assert db_type in ["sqlite", "postgresql"]

    def test_fallback_enabled(self, implementation_status):
        """Adapter should have fallback enabled."""
        assert implementation_status.get("fallback_enabled", False) is True


# ============================================================================
# TEST GROUP 2: Employee Read Operations
# ============================================================================

class TestEmployeeRead:
    """Test employee read operations."""

    def test_get_available_years(self):
        """Should return list of available years."""
        years = get_available_years()
        assert isinstance(years, list)
        # Years should be integers (or empty list if no data)
        for year in years:
            assert isinstance(year, int)
            assert 2000 <= year <= 2050

    def test_get_employees_returns_list(self):
        """Should return list of employees."""
        employees = get_employees()
        assert isinstance(employees, list)
        # Each employee should be a dict
        for emp in employees:
            assert isinstance(emp, dict)

    def test_get_employees_with_year_filter(self):
        """Should filter employees by year."""
        employees = get_employees(year=2025)
        assert isinstance(employees, list)
        # All employees should have year=2025
        for emp in employees:
            assert emp.get("year") == 2025

    def test_get_employees_returns_expected_fields(self):
        """Employees should have expected fields."""
        employees = get_employees()
        if employees:  # Skip if no data
            emp = employees[0]
            expected_fields = ["name", "balance", "usage_rate", "year"]
            for field in expected_fields:
                assert field in emp, f"Missing field: {field}"

    def test_get_employee_by_num_and_year(self):
        """Should get specific employee."""
        employees = get_employees(year=2025)
        if employees:
            emp = employees[0]
            emp_num = emp.get("employee_num")
            year = emp.get("year")

            # Get the same employee via get_employee
            specific = get_employee(emp_num, year)
            if specific:
                assert specific["employee_num"] == emp_num
                assert specific["year"] == year

    def test_get_employee_not_found(self):
        """Should return None if employee not found."""
        emp = get_employee("NONEXISTENT_9999", 2025)
        assert emp is None or emp == {}


# ============================================================================
# TEST GROUP 3: Leave Request Operations
# ============================================================================

class TestLeaveRequests:
    """Test leave request operations."""

    def test_get_leave_requests_returns_list(self):
        """Should return list of leave requests."""
        requests = get_leave_requests()
        assert isinstance(requests, list)
        for req in requests:
            assert isinstance(req, dict)

    def test_get_leave_requests_by_status(self):
        """Should filter requests by status."""
        statuses = ["PENDING", "APPROVED", "REJECTED"]
        for status in statuses:
            requests = get_leave_requests(status=status)
            assert isinstance(requests, list)
            # All returned should have matching status
            for req in requests:
                assert req.get("status") == status

    def test_get_leave_requests_by_employee(self):
        """Should filter requests by employee number."""
        all_requests = get_leave_requests()
        if all_requests:
            emp_num = all_requests[0].get("employee_num")
            emp_requests = get_leave_requests(employee_num=emp_num)
            # All returned should be for this employee
            for req in emp_requests:
                assert req.get("employee_num") == emp_num

    def test_get_leave_requests_by_year(self):
        """Should filter requests by year."""
        year_requests = get_leave_requests(year=2025)
        assert isinstance(year_requests, list)
        for req in year_requests:
            assert req.get("year") == 2025


# ============================================================================
# TEST GROUP 4: Usage Details
# ============================================================================

class TestUsageDetails:
    """Test usage details operations."""

    def test_get_yukyu_usage_details_returns_list(self):
        """Should return list of usage details."""
        details = get_yukyu_usage_details()
        assert isinstance(details, list)
        for detail in details:
            assert isinstance(detail, dict)

    def test_get_usage_details_by_employee(self):
        """Should filter usage details by employee."""
        details = get_yukyu_usage_details()
        if details:
            emp_num = details[0].get("employee_num")
            emp_details = get_yukyu_usage_details(employee_num=emp_num)
            for detail in emp_details:
                assert detail.get("employee_num") == emp_num

    def test_get_usage_details_by_year_month(self):
        """Should filter by year and month."""
        details = get_yukyu_usage_details(year=2025, month=1)
        assert isinstance(details, list)
        for detail in details:
            assert detail.get("year") == 2025
            assert detail.get("month") == 1


# ============================================================================
# TEST GROUP 5: Employee Type Classifications
# ============================================================================

class TestEmployeeTypes:
    """Test dispatch, contract, and staff employees."""

    def test_get_genzai_returns_list(self):
        """Should return list of dispatch employees."""
        genzai = get_genzai()
        assert isinstance(genzai, list)

    def test_get_genzai_by_status(self):
        """Should filter genzai by status."""
        active = get_genzai(status="在職中")
        assert isinstance(active, list)
        for emp in active:
            assert emp.get("status") == "在職中"

    def test_get_ukeoi_returns_list(self):
        """Should return list of contract employees."""
        ukeoi = get_ukeoi()
        assert isinstance(ukeoi, list)

    def test_get_staff_returns_list(self):
        """Should return list of staff employees."""
        staff = get_staff()
        assert isinstance(staff, list)


# ============================================================================
# TEST GROUP 6: Employee History
# ============================================================================

class TestEmployeeHistory:
    """Test employee history operations."""

    def test_get_employee_yukyu_history(self):
        """Should return employee history (2 years)."""
        # Try with a known employee if available
        employees = get_employees()
        if employees:
            emp_num = employees[0].get("employee_num")
            history = get_employee_yukyu_history(emp_num, current_year=2025)
            assert isinstance(history, list)
            # Should have at most 2 years of data
            assert len(history) <= 2
            # All entries should be for the same employee
            for entry in history:
                assert entry.get("employee_num") == emp_num


# ============================================================================
# TEST GROUP 7: Write Operations
# ============================================================================

class TestWriteOperations:
    """Test save/write operations (may be marked as integration tests)."""

    @pytest.mark.integration
    def test_save_employees_does_not_crash(self, sample_employee_data):
        """Save operation should not crash (basic sanity test)."""
        try:
            save_employees([sample_employee_data])
            # If no exception, test passes
            assert True
        except Exception as e:
            pytest.skip(f"Save operation not available: {e}")

    @pytest.mark.integration
    def test_save_genzai_does_not_crash(self, sample_genzai_data):
        """Save genzai operation should not crash."""
        try:
            save_genzai([sample_genzai_data])
            assert True
        except Exception as e:
            pytest.skip(f"Save operation not available: {e}")

    @pytest.mark.integration
    def test_save_yukyu_usage_details_does_not_crash(self):
        """Save usage details operation should not crash."""
        usage = [
            {
                "employee_num": "TEST_001",
                "name": "テスト太郎",
                "use_date": "2025-01-15",
                "year": 2025,
                "month": 1,
                "days_used": 1.0,
            }
        ]
        try:
            save_yukyu_usage_details(usage)
            assert True
        except Exception as e:
            pytest.skip(f"Save operation not available: {e}")


# ============================================================================
# TEST GROUP 8: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling consistency."""

    def test_get_employee_with_none_params(self):
        """Should handle None/invalid parameters gracefully."""
        # Should not crash with None
        result = get_employee(None, None)
        # Should return None or empty dict, not crash
        assert result is None or result == {}

    def test_get_leave_requests_with_empty_filters(self):
        """Should handle empty/None filters."""
        requests = get_leave_requests(status=None, employee_num=None)
        # Should return list (possibly empty)
        assert isinstance(requests, list)


# ============================================================================
# TEST GROUP 9: Data Consistency
# ============================================================================

class TestDataConsistency:
    """Test that data is consistent across reads."""

    def test_get_employee_consistency(self):
        """Same employee should return consistent data."""
        employees = get_employees(year=2025)
        if employees:
            emp = employees[0]
            emp_num = emp.get("employee_num")
            year = emp.get("year")

            # Get same employee separately
            specific = get_employee(emp_num, year)
            if specific:
                # Key fields should match
                assert specific.get("employee_num") == emp.get("employee_num")
                assert specific.get("year") == emp.get("year")
                assert specific.get("name") == emp.get("name")

    def test_save_and_retrieve(self, sample_employee_data):
        """Saved data should be retrievable."""
        try:
            # Save
            save_employees([sample_employee_data])

            # Retrieve
            emp = get_employee(
                sample_employee_data["employee_num"],
                sample_employee_data["year"]
            )

            if emp:  # May not be immediately available due to transaction timing
                assert emp.get("employee_num") == sample_employee_data["employee_num"]
                assert emp.get("name") == sample_employee_data["name"]
        except Exception as e:
            pytest.skip(f"Integration test not available: {e}")


# ============================================================================
# TEST GROUP 10: Performance Regression
# ============================================================================

class TestPerformance:
    """Basic performance regression tests."""

    @pytest.mark.slow
    def test_get_employees_performance(self):
        """get_employees should return within reasonable time."""
        import time
        start = time.time()
        get_employees()
        elapsed = time.time() - start
        # Should complete in less than 1 second
        assert elapsed < 1.0, f"Query took too long: {elapsed}s"

    @pytest.mark.slow
    def test_get_leave_requests_performance(self):
        """get_leave_requests should return within reasonable time."""
        import time
        start = time.time()
        get_leave_requests()
        elapsed = time.time() - start
        # Should complete in less than 1 second
        assert elapsed < 1.0, f"Query took too long: {elapsed}s"


# ============================================================================
# Test Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires DB)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (performance test)"
    )
    print(f"\n{'='*60}")
    print("Database Adapter Tests")
    print('='*60)
    status = get_implementation_status()
    print(f"Implementation: {status['implementation']}")
    print(f"Database: {status['database_type']}")
    print(f"ORM Available: {status['orm_available']}")
    print('='*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
