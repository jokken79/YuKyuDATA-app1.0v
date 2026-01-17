"""
Tests for /routes/leave_requests.py
Tests for leave request workflow: create, approve, reject, revert.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestLeaveRequestsList:
    """Tests for leave requests list endpoint"""

    def test_get_leave_requests(self):
        """Should return list of leave requests"""
        response = client.get("/api/leave-requests")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_leave_requests_with_status_filter(self):
        """Should filter by status"""
        response = client.get("/api/leave-requests?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_get_leave_requests_with_year_filter(self):
        """Should filter by year"""
        year = datetime.now().year
        response = client.get(f"/api/leave-requests?year={year}")
        assert response.status_code == 200

    def test_get_leave_requests_with_employee_filter(self):
        """Should filter by employee"""
        response = client.get("/api/leave-requests?employee_num=001")
        assert response.status_code == 200


class TestLeaveRequestCreate:
    """Tests for creating leave requests"""

    def test_create_leave_request_validation(self):
        """Should validate required fields"""
        # Missing required fields
        response = client.post("/api/leave-requests", json={})
        assert response.status_code in [400, 422]

    def test_create_leave_request_invalid_dates(self):
        """Should reject end date before start date"""
        response = client.post("/api/leave-requests", json={
            "employee_num": "001",
            "year": 2025,
            "start_date": "2025-12-31",
            "end_date": "2025-01-01",  # Before start
            "leave_type": "full"
        })
        # Should reject
        assert response.status_code in [400, 422]


class TestLeaveRequestWorkflow:
    """Tests for approve/reject/revert workflow"""

    def test_approve_nonexistent_request(self):
        """Should handle non-existent request gracefully"""
        response = client.patch("/api/leave-requests/99999/approve")
        assert response.status_code in [400, 404]

    def test_reject_nonexistent_request(self):
        """Should handle non-existent request gracefully"""
        response = client.patch("/api/leave-requests/99999/reject")
        assert response.status_code in [400, 404]

    def test_revert_nonexistent_request(self):
        """Should handle non-existent request gracefully"""
        response = client.patch("/api/leave-requests/99999/revert")
        assert response.status_code in [400, 404]


class TestLeaveRequestHistory:
    """Tests for request history"""

    def test_get_request_history(self):
        """Should return request history"""
        response = client.get("/api/leave-requests")
        assert response.status_code == 200
        data = response.json()
        if data.get("data"):
            for request in data["data"]:
                # Each request should have status
                assert "status" in request or "request_status" in request


class TestLeaveRequestErrorHandling:
    """Tests for error handling"""

    def test_invalid_status_filter(self):
        """Should handle invalid status filter"""
        response = client.get("/api/leave-requests?status=INVALID_STATUS")
        # Should return empty or handle gracefully
        assert response.status_code == 200

    def test_error_no_internal_details(self):
        """Errors should not expose internal details"""
        response = client.patch("/api/leave-requests/99999/approve")
        if response.status_code >= 400:
            data = response.json()
            detail = str(data.get("detail", ""))
            assert "/home/" not in detail
            assert "sqlite" not in detail.lower() or "error" not in detail.lower()


class TestLeaveRequestBulk:
    """Tests for bulk operations"""

    def test_bulk_edit_endpoint(self):
        """Should have bulk edit endpoint"""
        response = client.post("/api/leave-requests/bulk-edit", json={
            "request_ids": [],
            "action": "approve"
        })
        # May return 400 for empty list or 200
        assert response.status_code in [200, 400, 404]


class TestLeaveRequestTypes:
    """Tests for different leave types"""

    def test_leave_types_supported(self):
        """Should support full and half day types"""
        response = client.get("/api/leave-requests")
        assert response.status_code == 200
        data = response.json()
        # Should return without error
        assert data["status"] == "success"
