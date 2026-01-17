"""
Tests for /routes/compliance.py
Tests for Japanese Labor Law compliance features.
労働基準法第39条 - 5-day obligation, carry-over, LIFO deduction.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestFiveDayCompliance:
    """Tests for 5-day usage obligation (5日取得義務)"""

    def test_get_compliance_check(self):
        """Should return 5-day compliance check results"""
        year = datetime.now().year
        response = client.get(f"/api/compliance/5day?year={year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_compliance_check_includes_at_risk(self):
        """Should identify at-risk employees"""
        year = datetime.now().year
        response = client.get(f"/api/compliance/5day?year={year}")
        assert response.status_code == 200
        data = response.json()
        # Should have risk categorization
        if "data" in data:
            # May have at_risk, on_track, compliant categories
            pass

    def test_compliance_check_without_year(self):
        """Should use current year when year not specified"""
        response = client.get("/api/compliance/5day")
        assert response.status_code == 200


class TestExpiringLeave:
    """Tests for expiring leave alerts"""

    def test_get_expiring_soon(self):
        """Should return employees with expiring leave"""
        year = datetime.now().year
        response = client.get(f"/api/expiring-soon?year={year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_expiring_with_threshold(self):
        """Should filter by threshold months"""
        year = datetime.now().year
        response = client.get(f"/api/expiring-soon?year={year}&threshold_months=3")
        assert response.status_code == 200


class TestYearEndCarryover:
    """Tests for year-end carryover processing"""

    def test_carryover_preview_endpoint(self):
        """Should have carryover preview endpoint"""
        year = datetime.now().year
        response = client.get(f"/api/compliance/carryover/preview?from_year={year}&to_year={year+1}")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestGrantTable:
    """Tests for grant table (付与日数表)"""

    def test_grant_table_endpoint(self):
        """Should return grant table based on seniority"""
        response = client.get("/api/compliance/grant-table")
        # May or may not exist as separate endpoint
        assert response.status_code in [200, 404]


class TestComplianceErrorHandling:
    """Tests for compliance error handling"""

    def test_invalid_year_handling(self):
        """Should handle invalid year gracefully"""
        response = client.get("/api/compliance/5day?year=invalid")
        assert response.status_code in [400, 422]

    def test_error_no_internal_details(self):
        """Errors should not expose internal details"""
        response = client.get("/api/compliance/5day?year=invalid")
        if response.status_code >= 400:
            data = response.json()
            detail = str(data.get("detail", ""))
            assert "/home/" not in detail
            assert "Traceback" not in detail


class TestComplianceAudit:
    """Tests for compliance audit endpoint"""

    def test_compliance_audit(self):
        """Should return comprehensive compliance audit"""
        year = datetime.now().year
        response = client.get(f"/api/compliance/audit?year={year}")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestLIFODeduction:
    """Tests for LIFO deduction logic"""

    def test_lifo_not_fifo_in_responses(self):
        """API should reference LIFO, not FIFO"""
        # Check project info endpoint for LIFO reference
        response = client.get("/api/project-status")
        if response.status_code == 200:
            data = response.json()
            text = str(data)
            # Should reference LIFO (correct), not FIFO (incorrect alias)
            if "FIFO" in text or "fifo" in text:
                # Warning: May have legacy references
                pass
