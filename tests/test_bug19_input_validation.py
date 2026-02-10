"""
BUG #19-22: Input Validation Tests

Verifica que los parámetros de query se validen correctamente:
- Year validation (2000-2100)
- Month validation (1-12)
- Min/Max constraints
- String length limits
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestInputValidation_YearParameter:
    """Test year parameter validation"""

    def test_invalid_year_too_small(self):
        """Year < 2000 should be rejected"""
        response = client.get("/analytics/dashboard/1999")
        assert response.status_code in [422, 400], "Year too small should fail validation"

    def test_invalid_year_too_large(self):
        """Year > 2100 should be rejected"""
        response = client.get("/analytics/dashboard/2101")
        assert response.status_code in [422, 400], "Year too large should fail validation"

    def test_valid_year_boundaries(self):
        """Valid years 2000-2100 should be accepted (with auth)"""
        # Login first
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test boundary values
        for year in [2000, 2050, 2100]:
            response = client.get(f"/analytics/dashboard/{year}", headers=headers)
            # Should not return 422 for valid year
            assert response.status_code != 422, f"Year {year} should be valid"


class TestInputValidation_MonthParameter:
    """Test month parameter validation"""

    def test_invalid_month_zero(self):
        """Month 0 should be rejected"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/reports/monthly/2025/0", headers=headers)
        assert response.status_code in [422, 400], "Month 0 should fail validation"

    def test_invalid_month_13(self):
        """Month 13 should be rejected"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/reports/monthly/2025/13", headers=headers)
        assert response.status_code in [422, 400], "Month 13 should fail validation"

    def test_valid_month_boundaries(self):
        """Valid months 1-12 should be accepted"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for month in [1, 6, 12]:
            response = client.get(f"/reports/monthly/2025/{month}", headers=headers)
            # Should not return 422 for valid month
            assert response.status_code != 422, f"Month {month} should be valid"


class TestInputValidation_StringParameters:
    """Test string parameter validation"""

    def test_empty_employee_num_rejected(self):
        """Empty employee_num should be rejected"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Query with empty employee_num
        response = client.get("/yukyu/employee-summary//2025", headers=headers)
        # Should either return 404 (not found) or 422 (validation error)
        assert response.status_code in [404, 422]

    def test_max_length_employee_num(self):
        """Employee num > 10 chars should be rejected"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Employee num too long
        long_emp_num = "a" * 20
        response = client.get(f"/yukyu/employee-summary/{long_emp_num}/2025", headers=headers)
        assert response.status_code in [422, 400], "Employee num > 10 chars should fail"


class TestInputValidation_LimitParameters:
    """Test limit/offset parameter validation"""

    def test_limit_max_constraint(self):
        """Limit > max should be rejected"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Limit way too high
        response = client.get("/system/audit-log?limit=10000", headers=headers)
        assert response.status_code in [422, 400], "Limit > 500 should fail validation"

    def test_negative_limit_rejected(self):
        """Negative limit should be rejected"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code != 200:
            pytest.skip("Could not authenticate")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/system/audit-log?limit=-1", headers=headers)
        assert response.status_code in [422, 400], "Negative limit should fail"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
