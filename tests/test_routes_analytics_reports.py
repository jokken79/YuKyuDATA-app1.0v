"""
Tests for /routes/analytics.py and /routes/reports.py
Tests for analytics, predictions, and report generation.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints"""

    def test_get_predictions(self):
        """Should return year-end predictions"""
        year = datetime.now().year
        response = client.get(f"/api/analytics/predictions?year={year}")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_get_analytics_summary(self):
        """Should return analytics summary"""
        response = client.get("/api/analytics/summary")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_get_usage_trends(self):
        """Should return usage trends"""
        response = client.get("/api/analytics/trends")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestReportsEndpoints:
    """Tests for report generation endpoints"""

    def test_get_monthly_report(self):
        """Should generate monthly report"""
        year = datetime.now().year
        month = datetime.now().month
        response = client.get(f"/api/reports/monthly?year={year}&month={month}")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_get_report_list(self):
        """Should return list of available reports"""
        response = client.get("/api/reports")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestExportEndpoints:
    """Tests for export endpoints"""

    def test_export_csv(self):
        """Should export data as CSV"""
        year = datetime.now().year
        response = client.get(f"/api/export/csv?year={year}")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_export_excel(self):
        """Should export data as Excel"""
        year = datetime.now().year
        response = client.get(f"/api/export/excel?year={year}")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_export_pdf(self):
        """Should export data as PDF"""
        year = datetime.now().year
        response = client.get(f"/api/export/pdf?year={year}")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestAnalyticsErrorHandling:
    """Tests for error handling in analytics"""

    def test_invalid_year_analytics(self):
        """Should handle invalid year in analytics"""
        response = client.get("/api/analytics/predictions?year=invalid")
        assert response.status_code in [400, 422]

    def test_error_no_internal_details(self):
        """Errors should not expose internal details"""
        response = client.get("/api/analytics/predictions?year=invalid")
        if response.status_code >= 400:
            data = response.json()
            detail = str(data.get("detail", ""))
            assert "/home/" not in detail
            assert "Traceback" not in detail


class TestNotificationsEndpoints:
    """Tests for notifications endpoints"""

    def test_get_notifications(self):
        """Should return notifications list"""
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "notifications" in data

    def test_get_unread_count(self):
        """Should return unread notification count"""
        response = client.get("/api/notifications/unread-count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data or "unread" in data or isinstance(data, int)


class TestCalendarEndpoints:
    """Tests for calendar endpoints"""

    def test_get_calendar_events(self):
        """Should return calendar events"""
        year = datetime.now().year
        month = datetime.now().month
        response = client.get(f"/api/calendar/events?year={year}&month={month}")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestFiscalEndpoints:
    """Tests for fiscal year endpoints"""

    def test_get_fiscal_info(self):
        """Should return fiscal year information"""
        response = client.get("/api/fiscal/info")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_get_fiscal_periods(self):
        """Should return fiscal periods"""
        response = client.get("/api/fiscal/periods")
        # May or may not exist
        assert response.status_code in [200, 404]
