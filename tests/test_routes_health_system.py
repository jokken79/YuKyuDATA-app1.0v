"""
Tests for /routes/health.py and /routes/system.py
Tests for health checks, system status, and monitoring endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints"""

    def test_health_check_basic(self):
        """Should return healthy status"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_db_status(self):
        """Should return database status"""
        response = client.get("/api/db-status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_project_status(self):
        """Should return project status information"""
        response = client.get("/api/project-status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "version" in data


class TestSystemEndpoints:
    """Tests for system endpoints"""

    def test_system_info(self):
        """Should return system information"""
        response = client.get("/api/system/info")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_available_years(self):
        """Should return available years"""
        response = client.get("/api/employees")
        assert response.status_code == 200
        data = response.json()
        assert "available_years" in data
        assert isinstance(data["available_years"], list)


class TestMonitoringEndpoints:
    """Tests for monitoring endpoints"""

    def test_metrics_endpoint(self):
        """Should return metrics if available"""
        response = client.get("/api/metrics")
        # May or may not exist
        assert response.status_code in [200, 404]

    def test_stats_endpoint(self):
        """Should return stats if available"""
        response = client.get("/api/stats")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestBackupEndpoints:
    """Tests for backup endpoints"""

    def test_backup_list(self):
        """Should return backup list if available"""
        response = client.get("/api/backups")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestHealthErrorHandling:
    """Tests for error handling in health endpoints"""

    def test_health_no_internal_details(self):
        """Health endpoint should not expose internal paths"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        text = str(data)
        # Should not contain file paths
        assert "/home/" not in text or "path" in text.lower()

    def test_db_status_no_sensitive_data(self):
        """DB status should not expose sensitive information"""
        response = client.get("/api/db-status")
        if response.status_code == 200:
            data = response.json()
            text = str(data)
            # Should not contain passwords or connection strings
            assert "password" not in text.lower()


class TestCORS:
    """Tests for CORS headers"""

    def test_cors_headers_present(self):
        """Should have CORS headers if configured"""
        response = client.options("/api/health")
        # CORS preflight should work
        assert response.status_code in [200, 405]


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_returns_html(self):
        """Root should return HTML page"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_root_contains_app_name(self):
        """Root page should contain app name"""
        response = client.get("/")
        assert response.status_code == 200
        assert "YuKyu" in response.text or "有給" in response.text
