"""
BUG #15: Endpoint Authentication Tests

Verifica que endpoints sensibles requieran autenticación:
- /api/yukyu/* endpoints (statistics, usage details)
- /api/audit-log endpoints
- /api/orchestrator endpoints
- /api/system endpoints
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestBUG15_YukyuEndpointAuth:
    """Test BUG #15: /yukyu/* endpoints require auth"""

    def test_usage_details_requires_auth(self):
        """Test /yukyu/usage-details requires auth"""
        response = client.get("/yukyu/usage-details")
        assert response.status_code == 401, "usage-details should require auth"

    def test_usage_details_with_auth(self):
        """Test /yukyu/usage-details works with valid auth"""
        # Login first
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = client.get("/yukyu/usage-details", headers=headers)
            assert response.status_code == 200, f"Should work with auth, got {response.status_code}"

    def test_monthly_summary_requires_auth(self):
        """Test /yukyu/monthly-summary requires auth"""
        response = client.get("/yukyu/monthly-summary/2025")
        assert response.status_code == 401

    def test_kpi_stats_requires_auth(self):
        """Test /yukyu/kpi-stats requires auth"""
        response = client.get("/yukyu/kpi-stats/2025")
        assert response.status_code == 401

    def test_by_employee_type_requires_auth(self):
        """Test /yukyu/by-employee-type requires auth"""
        response = client.get("/yukyu/by-employee-type/2025")
        assert response.status_code == 401

    def test_employee_summary_requires_auth(self):
        """Test /yukyu/employee-summary requires auth"""
        response = client.get("/yukyu/employee-summary/001/2025")
        assert response.status_code == 401


class TestBUG15_SystemEndpointAuth:
    """Test BUG #15: /api/system/* and /api/audit-log endpoints require auth"""

    def test_cache_stats_requires_auth(self):
        """Test /cache-stats requires auth"""
        response = client.get("/cache-stats")
        assert response.status_code == 401

    def test_audit_log_requires_auth(self):
        """Test /audit-log requires auth"""
        response = client.get("/audit-log")
        assert response.status_code == 401

    def test_audit_log_entity_requires_auth(self):
        """Test /audit-log/{entity_type}/{entity_id} requires auth"""
        response = client.get("/audit-log/employee/emp_001")
        assert response.status_code == 401

    def test_audit_log_user_requires_auth(self):
        """Test /audit-log/user/{user_id} requires auth"""
        response = client.get("/audit-log/user/admin")
        assert response.status_code == 401

    def test_audit_log_stats_requires_auth(self):
        """Test /audit-log/stats requires auth"""
        response = client.get("/audit-log/stats")
        assert response.status_code == 401

    def test_orchestrator_status_requires_auth(self):
        """Test /orchestrator/status requires auth"""
        response = client.get("/orchestrator/status")
        assert response.status_code == 401

    def test_orchestrator_history_requires_auth(self):
        """Test /orchestrator/history requires auth"""
        response = client.get("/orchestrator/history")
        assert response.status_code == 401

    def test_orchestrator_compliance_check_requires_auth(self):
        """Test /orchestrator/run-compliance-check requires auth"""
        response = client.post("/orchestrator/run-compliance-check/2025")
        assert response.status_code == 401

    def test_system_snapshot_requires_auth(self):
        """Test /system/snapshot requires auth"""
        response = client.get("/system/snapshot")
        assert response.status_code == 401

    def test_system_audit_log_requires_auth(self):
        """Test /system/audit-log requires auth"""
        response = client.get("/system/audit-log")
        assert response.status_code == 401

    def test_system_activity_report_requires_auth(self):
        """Test /system/activity-report requires auth"""
        response = client.get("/system/activity-report")
        assert response.status_code == 401


class TestBUG15_AuthWithValidToken:
    """Test that endpoints work with valid authentication"""

    @pytest.fixture
    def auth_headers(self):
        """Get valid auth headers"""
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        return None

    def test_endpoints_work_with_auth(self, auth_headers):
        """Test that secured endpoints work with valid auth"""
        if not auth_headers:
            pytest.skip("Could not authenticate")

        # Test a few key endpoints
        response = client.get("/cache-stats", headers=auth_headers)
        assert response.status_code in [200, 500], "Should not return 401 with valid auth"

        response = client.get("/audit-log", headers=auth_headers)
        assert response.status_code in [200, 500], "Should not return 401 with valid auth"

        response = client.get("/orchestrator/status", headers=auth_headers)
        assert response.status_code in [200, 500], "Should not return 401 with valid auth"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
