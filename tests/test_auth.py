"""
YuKyu Premium - Authentication Tests
認証テスト - JWT認証システムのテスト
"""

import pytest
from fastapi.testclient import TestClient


class TestAuthentication:
    """Authentication system tests"""

    def test_login_success(self, client: TestClient):
        """Valid credentials return JWT token"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "admin"
        assert data["user"]["role"] == "admin"

    def test_login_invalid_password(self, client: TestClient):
        """Invalid password returns 401"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_invalid_username(self, client: TestClient):
        """Invalid username returns 401"""
        response = client.post(
            "/api/auth/login",
            json={"username": "unknown", "password": "admin123"},
        )
        assert response.status_code == 401

    def test_login_missing_fields(self, client: TestClient):
        """Missing fields returns 422"""
        response = client.post("/api/auth/login", json={"username": "admin"})
        assert response.status_code == 422

    def test_verify_valid_token(self, client: TestClient, auth_headers):
        """Valid token passes verification"""
        response = client.get("/api/auth/verify", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["user"]["username"] == "admin"

    def test_verify_no_token(self, client: TestClient):
        """No token returns valid=False"""
        response = client.get("/api/auth/verify")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_verify_invalid_token(self, client: TestClient):
        """Invalid token returns valid=False"""
        response = client.get(
            "/api/auth/verify", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    def test_get_me_with_valid_token(self, client: TestClient, auth_headers):
        """Get current user info with valid token"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "admin"

    def test_get_me_without_token(self, client: TestClient):
        """Get me without token returns 401"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Tests for endpoints that require authentication"""

    def test_reset_requires_admin(self, client: TestClient):
        """Reset endpoint requires authentication"""
        response = client.delete("/api/reset")
        assert response.status_code == 401

    def test_reset_with_admin_token(self, client: TestClient, auth_headers):
        """Reset works with admin token"""
        response = client.delete("/api/reset", headers=auth_headers)
        assert response.status_code == 200

    def test_reset_genzai_requires_admin(self, client: TestClient):
        """Reset genzai requires authentication"""
        response = client.delete("/api/reset-genzai")
        assert response.status_code == 401

    def test_reset_ukeoi_requires_admin(self, client: TestClient):
        """Reset ukeoi requires authentication"""
        response = client.delete("/api/reset-ukeoi")
        assert response.status_code == 401

    def test_reset_staff_requires_admin(self, client: TestClient):
        """Reset staff requires authentication"""
        response = client.delete("/api/reset-staff")
        assert response.status_code == 401

    def test_cleanup_exports_requires_admin(self, client: TestClient):
        """Cleanup exports requires authentication"""
        response = client.delete("/api/export/cleanup")
        assert response.status_code == 401

    def test_data_endpoints_require_token(self, client: TestClient):
        """Protected endpoints now return 401 without token"""
        assert client.get("/api/employees").status_code == 401
        assert client.get("/api/genzai").status_code == 401
        assert client.get("/api/ukeoi").status_code == 401

    def test_data_endpoints_with_token(self, client: TestClient, auth_headers):
        """Protected endpoints return 200 with token"""
        assert client.get("/api/employees", headers=auth_headers).status_code == 200
        assert client.get("/api/genzai", headers=auth_headers).status_code == 200
        assert client.get("/api/ukeoi", headers=auth_headers).status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
