"""
YuKyu Premium - Authentication Tests
認証テスト - JWT認証システムのテスト
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestAuthentication:
    """Authentication system tests"""

    def test_login_success(self):
        """Valid credentials return JWT token"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    def test_login_invalid_password(self):
        """Invalid password returns 401"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_invalid_username(self):
        """Invalid username returns 401"""
        response = client.post("/api/auth/login", json={
            "username": "unknown",
            "password": "admin123"
        })
        assert response.status_code == 401

    def test_login_missing_fields(self):
        """Missing fields returns 422"""
        response = client.post("/api/auth/login", json={
            "username": "admin"
        })
        assert response.status_code == 422

    def test_verify_valid_token(self):
        """Valid token passes verification"""
        # First login to get token
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]

        # Verify token
        response = client.get("/api/auth/verify", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user"]["username"] == "admin"

    def test_verify_no_token(self):
        """No token returns valid=False"""
        response = client.get("/api/auth/verify")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_verify_invalid_token(self):
        """Invalid token returns valid=False"""
        response = client.get("/api/auth/verify", headers={
            "Authorization": "Bearer invalid-token"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_get_me_with_valid_token(self):
        """Get current user info with valid token"""
        # First login
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]

        # Get user info
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "admin"

    def test_get_me_without_token(self):
        """Get me without token returns 401"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Tests for endpoints that require authentication"""

    def get_admin_token(self):
        """Helper to get admin token"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        return response.json()["access_token"]

    def test_reset_requires_admin(self):
        """Reset endpoint requires admin authentication"""
        # Without token
        response = client.delete("/api/reset")
        assert response.status_code == 401

    def test_reset_with_admin_token(self):
        """Reset works with admin token"""
        token = self.get_admin_token()
        response = client.delete("/api/reset", headers={
            "Authorization": f"Bearer {token}"
        })
        # Should succeed (even if DB is already empty)
        assert response.status_code == 200

    def test_reset_genzai_requires_admin(self):
        """Reset genzai requires admin authentication"""
        response = client.delete("/api/reset-genzai")
        assert response.status_code == 401

    def test_reset_ukeoi_requires_admin(self):
        """Reset ukeoi requires admin authentication"""
        response = client.delete("/api/reset-ukeoi")
        assert response.status_code == 401

    def test_reset_staff_requires_admin(self):
        """Reset staff requires admin authentication"""
        response = client.delete("/api/reset-staff")
        assert response.status_code == 401

    def test_cleanup_exports_requires_admin(self):
        """Cleanup exports requires admin authentication"""
        response = client.delete("/api/export/cleanup")
        assert response.status_code == 401

    def test_public_endpoints_still_work(self):
        """Public endpoints don't require authentication"""
        # These should work without auth
        response = client.get("/api/employees")
        assert response.status_code == 200

        response = client.get("/api/genzai")
        assert response.status_code == 200

        response = client.get("/api/ukeoi")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
