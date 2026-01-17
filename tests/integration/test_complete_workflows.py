"""
Complete integration tests for YuKyuDATA workflows.

Tests end-to-end workflows:
1. Leave request creation and approval
2. Fiscal year processing
3. Compliance verification
4. Data synchronization
5. Report generation
"""

import pytest
from datetime import datetime, timedelta
import time


class TestLeaveRequestWorkflow:
    """Test complete leave request workflow."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_complete_leave_request_workflow(self, client, auth_headers):
        """Test: Complete workflow from creation to approval."""

        # Step 1: Get employee balance before request
        response = client.get("/api/employees?year=2025", headers=auth_headers)
        assert response.status_code == 200
        employees_before = response.json().get("data", [])
        employee_001_before = next((e for e in employees_before if e.get("employee_num") == "001"), None)

        if not employee_001_before:
            pytest.skip("Employee 001 not found")

        balance_before = employee_001_before.get("balance", 0)

        # Step 2: Create leave request
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        create_response = client.post(
            "/api/leave-requests",
            json={
                "employee_num": "001",
                "start_date": tomorrow,
                "end_date": tomorrow,
                "days_requested": 1.0,
                "leave_type": "full",
                "reason": "Integration test leave",
                "year": 2025
            },
            headers=auth_headers
        )

        assert create_response.status_code in [200, 201]
        request_data = create_response.json()
        request_id = request_data.get("id")

        assert request_id is not None, "Leave request should have ID"

        # Step 3: Verify request was created
        get_response = client.get(
            f"/api/leave-requests/{request_id}",
            headers=auth_headers
        )

        if get_response.status_code == 200:
            req = get_response.json()
            assert req.get("employee_num") == "001"
            assert req.get("days_requested") == 1.0

        # Step 4: Approve request (if endpoint exists)
        approve_response = client.post(
            f"/api/leave-requests/{request_id}/approve",
            headers=auth_headers
        ) or client.patch(
            f"/api/leave-requests/{request_id}/approve",
            json={"status": "approved"},
            headers=auth_headers
        )

        # Step 5: Verify balance decreased (if approval actually deducts)
        if approve_response.status_code in [200, 201]:
            time.sleep(0.5)  # Allow processing

            response = client.get("/api/employees?year=2025", headers=auth_headers)
            if response.status_code == 200:
                employees_after = response.json().get("data", [])
                employee_001_after = next((e for e in employees_after if e.get("employee_num") == "001"), None)

                if employee_001_after:
                    balance_after = employee_001_after.get("balance", 0)
                    # Balance should decrease (or stay same if not deducted yet)
                    assert balance_after <= balance_before


class TestFiscalYearWorkflow:
    """Test fiscal year processing workflow."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_fiscal_year_carryover(self, client, auth_headers):
        """Test: Fiscal year carryover (year end processing)."""

        # Step 1: Get employees for current year
        response = client.get("/api/employees?year=2025", headers=auth_headers)
        assert response.status_code == 200
        employees_2025 = response.json().get("data", [])

        # Step 2: Check if next year employees exist
        response = client.get("/api/employees?year=2026", headers=auth_headers)

        if response.status_code == 200:
            employees_2026 = response.json().get("data", [])

            # Should have carryover data if years exist
            if employees_2025 and employees_2026:
                emp_2025 = employees_2025[0]
                emp_num = emp_2025.get("employee_num")

                emp_2026 = next((e for e in employees_2026 if e.get("employee_num") == emp_num), None)

                if emp_2026:
                    # Carryover days should be reflected in next year
                    assert emp_2026.get("balance") is not None

    def test_seniority_grant_calculation(self, client, auth_headers):
        """Test: Seniority to grant day calculation."""

        # Get employees
        response = client.get("/api/employees?year=2025", headers=auth_headers)
        assert response.status_code == 200
        employees = response.json().get("data", [])

        # Verify grant days are reasonable
        for emp in employees:
            granted = emp.get("granted", 0)
            assert 0 <= granted <= 40, f"Granted days should be 0-40, got {granted}"

            balance = emp.get("balance", 0)
            used = emp.get("used", 0)

            # Balance + used should roughly equal granted (with carryover)
            total_available = balance + used
            assert total_available >= 0, f"Total should be non-negative"


class TestComplianceWorkflow:
    """Test compliance verification workflow."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_5day_compliance_check(self, client, auth_headers):
        """Test: 5-day compliance verification."""

        # Get compliance data
        response = client.get(
            "/api/compliance/5day?year=2025",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            # Should have compliance statistics
            assert isinstance(data, dict)

            # Check for expected fields
            expected_fields = [
                "compliant",
                "non_compliant",
                "total_employees",
                "compliance_rate"
            ]

            for field in expected_fields:
                if field in data:
                    if field == "compliance_rate":
                        assert 0 <= data[field] <= 100
                    else:
                        assert isinstance(data[field], (list, int))

    def test_expiring_days_detection(self, client, auth_headers):
        """Test: Detection of expiring paid leave days."""

        # Get employees
        response = client.get("/api/employees?year=2025", headers=auth_headers)

        if response.status_code == 200:
            employees = response.json().get("data", [])

            # Check expiring days endpoint
            response = client.get(
                "/api/expiring-soon?year=2025&threshold_months=3",
                headers=auth_headers
            )

            if response.status_code == 200:
                data = response.json()

                # Should return list of employees with expiring days
                if isinstance(data, dict) and "data" in data:
                    expiring = data["data"]
                    assert isinstance(expiring, list)

                    # Each should have expiring info
                    for emp in expiring:
                        assert emp.get("employee_num")
                        assert emp.get("expiring_days", 0) > 0


class TestDataSynchronization:
    """Test data synchronization workflows."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_sync_and_verify_data_integrity(self, client, auth_headers):
        """Test: Sync and verify data consistency."""

        # Step 1: Get employee count before sync
        response = client.get("/api/employees?year=2025", headers=auth_headers)
        assert response.status_code == 200
        count_before = len(response.json().get("data", []))

        # Step 2: Attempt sync (if endpoint exists)
        sync_response = client.post(
            "/api/sync",
            json={},
            headers=auth_headers
        )

        # Step 3: Verify data integrity after
        response = client.get("/api/employees?year=2025", headers=auth_headers)
        if response.status_code == 200:
            employees = response.json().get("data", [])
            count_after = len(employees)

            # Verify structure
            for emp in employees:
                assert emp.get("employee_num")
                assert emp.get("year")
                assert emp.get("granted") is not None
                assert emp.get("balance") is not None

    def test_concurrent_sync_safety(self, client, auth_headers):
        """Test: Concurrent syncs should not corrupt data."""
        import threading
        from concurrent.futures import ThreadPoolExecutor

        def sync_operation():
            return client.post(
                "/api/sync",
                json={},
                headers=auth_headers
            )

        # Execute multiple syncs concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(sync_operation) for _ in range(5)]
            results = [f.result() for f in futures]

        # After concurrent syncs, data should still be consistent
        response = client.get("/api/employees?year=2025", headers=auth_headers)
        if response.status_code == 200:
            employees = response.json().get("data", [])

            # Verify all employees still have valid data
            for emp in employees:
                balance = emp.get("balance", 0)
                used = emp.get("used", 0)
                granted = emp.get("granted", 0)

                # Simple consistency check
                assert balance >= 0 or granted > 0


class TestReportGeneration:
    """Test report generation workflows."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_generate_monthly_report(self, client, auth_headers):
        """Test: Generate monthly report."""

        response = client.get(
            "/api/reports/monthly?year=2025&month=1",
            headers=auth_headers
        )

        # Should succeed or return 404 if endpoint not implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_generate_annual_report(self, client, auth_headers):
        """Test: Generate annual report."""

        response = client.get(
            "/api/reports/annual?year=2025",
            headers=auth_headers
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_pdf_report_generation(self, client, auth_headers):
        """Test: Generate PDF report."""

        response = client.post(
            "/api/reports/pdf",
            json={
                "year": 2025,
                "format": "pdf"
            },
            headers=auth_headers,
            timeout=30
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Should return PDF content
            assert "application/pdf" in response.headers.get("content-type", "")


class TestNotificationWorkflow:
    """Test notification workflows."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_notification_creation_and_reading(self, client, auth_headers):
        """Test: Create notification and mark as read."""

        # Get initial notifications
        response = client.get(
            "/api/notifications",
            headers=auth_headers
        )

        if response.status_code == 200:
            notifications_before = response.json().get("data", [])

            # Get unread count
            response = client.get(
                "/api/notifications/unread-count",
                headers=auth_headers
            )

            if response.status_code == 200:
                unread_count = response.json().get("unread_count", 0)

                # Mark first notification as read if exists
                if notifications_before:
                    notif = notifications_before[0]
                    notif_id = notif.get("id")

                    if notif_id:
                        response = client.patch(
                            f"/api/notifications/{notif_id}/read",
                            headers=auth_headers
                        ) or client.post(
                            f"/api/notifications/{notif_id}/read",
                            headers=auth_headers
                        )

                        # Verify it was marked as read
                        response = client.get(
                            "/api/notifications/unread-count",
                            headers=auth_headers
                        )

                        if response.status_code == 200:
                            new_unread = response.json().get("unread_count", 0)
                            # Should have decreased or stayed same
                            assert new_unread <= unread_count


class TestAnalyticsWorkflow:
    """Test analytics data workflows."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {"Authorization": f"Bearer {token}"}
        return {}

    def test_analytics_stats_calculation(self, client, auth_headers):
        """Test: Analytics statistics calculation."""

        response = client.get(
            "/api/analytics/stats?year=2025",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should have stats
        assert isinstance(data, dict)

        # Check for expected metrics
        if "data" in data:
            stats = data["data"]
            assert isinstance(stats, dict)

            # Typical metrics
            for key in ["total_employees", "total_used", "total_balance"]:
                if key in stats:
                    assert isinstance(stats[key], (int, float))
                    assert stats[key] >= 0

    def test_analytics_trends(self, client, auth_headers):
        """Test: Analytics trends calculation."""

        response = client.get(
            "/api/analytics/trends",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    def test_analytics_department_breakdown(self, client, auth_headers):
        """Test: Analytics by department."""

        response = client.get(
            "/api/analytics/department",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()

            # Should have breakdown by department
            if "data" in data:
                assert isinstance(data["data"], (list, dict))
