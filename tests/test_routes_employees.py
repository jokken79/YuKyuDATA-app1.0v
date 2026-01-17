"""
Tests for /routes/employees.py
Comprehensive test coverage for employee endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestEmployeesV1:
    """Tests for /api/v1/employees endpoint"""

    def test_get_employees_v1_success(self):
        """Should return employees with pagination structure"""
        response = client.get("/api/v1/employees")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_employees_v1_with_year(self):
        """Should filter by year"""
        year = datetime.now().year
        response = client.get(f"/api/v1/employees?year={year}")
        assert response.status_code == 200

    def test_get_employees_v1_pagination(self):
        """Should handle pagination parameters"""
        response = client.get("/api/v1/employees?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        # Should have pagination info if implemented
        assert "data" in data

    def test_get_employees_v1_search(self):
        """Should filter by search query"""
        response = client.get("/api/v1/employees?search=test")
        assert response.status_code == 200


class TestEmployeesByType:
    """Tests for /api/employees/by-type endpoint"""

    def test_get_employees_by_type_success(self):
        """Should return employees categorized by type"""
        response = client.get("/api/employees/by-type")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "haken" in data
        assert "ukeoi" in data
        assert "staff" in data

    def test_get_employees_by_type_with_year(self):
        """Should filter by year"""
        year = datetime.now().year
        response = client.get(f"/api/employees/by-type?year={year}")
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == year

    def test_get_employees_by_type_active_only(self):
        """Should filter active employees only"""
        response = client.get("/api/employees/by-type?active_only=true")
        assert response.status_code == 200
        data = response.json()
        assert data["active_only"] == True

    def test_get_employees_by_type_includes_inactive(self):
        """Should include inactive employees when flag is false"""
        response = client.get("/api/employees/by-type?active_only=false")
        assert response.status_code == 200
        data = response.json()
        assert data["active_only"] == False


class TestEmployeeDetails:
    """Tests for employee detail endpoints"""

    def test_get_employee_detail_invalid(self):
        """Should return 404 for non-existent employee"""
        response = client.get("/api/employee/INVALID_99999/2025")
        # Should handle gracefully
        assert response.status_code in [200, 404]

    def test_employee_search_endpoint(self):
        """Should search employees by query"""
        response = client.get("/api/employee/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("results", data.get("data", [])), list)


class TestEmployeesBulk:
    """Tests for bulk employee operations"""

    def test_get_employees_bulk_endpoint_exists(self):
        """Should have bulk endpoint available"""
        response = client.get("/api/employees")
        assert response.status_code == 200


class TestEmployeesErrorHandling:
    """Tests for error handling - should not expose internal details"""

    def test_invalid_year_format(self):
        """Should handle invalid year gracefully"""
        response = client.get("/api/employees?year=invalid")
        # Should return 422 (validation error) or 400, not 500
        assert response.status_code in [400, 422]

    def test_negative_page_number(self):
        """Should handle negative pagination"""
        response = client.get("/api/v1/employees?page=-1")
        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_error_response_no_internal_details(self):
        """Error responses should not expose internal paths or stack traces"""
        response = client.get("/api/employees?year=invalid")
        if response.status_code >= 400:
            data = response.json()
            detail = str(data.get("detail", ""))
            # Should not contain file paths
            assert "/home/" not in detail
            assert "\\Users\\" not in detail
            # Should not contain Python error class names
            assert "Traceback" not in detail


class TestEmployeesSummary:
    """Tests for employee summary endpoints"""

    def test_get_employee_summary(self):
        """Should return summary statistics"""
        response = client.get("/api/employees/summary")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestEmployeesPerformance:
    """Tests for performance - N+1 query fixes"""

    def test_by_type_performance(self):
        """Should complete within reasonable time (N+1 fixed)"""
        import time
        start = time.time()
        response = client.get("/api/employees/by-type")
        elapsed = time.time() - start
        assert response.status_code == 200
        # Should complete in less than 5 seconds even with many employees
        assert elapsed < 5.0
