"""
Integration Tests for Authentication Endpoints
Tests the complete auth flow: login, logout, token refresh, etc.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)


class TestAuthLogin:
    """Test /api/auth/login endpoint"""
    
    def test_login_success_admin(self):
        """Test successful login with admin credentials"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Verify token is not empty
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0
    
    def test_login_success_demo_user(self):
        """Test successful login with demo user"""
        response = client.post("/api/auth/login", json={
            "username": "demo",
            "password": "demo123456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_login_invalid_username(self):
        """Test login with invalid username"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_login_invalid_password(self):
        """Test login with invalid password"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    def test_login_missing_fields(self):
        """Test login with missing required fields"""
        response = client.post("/api/auth/login", json={
            "username": "admin"
            # password missing
        })
        
        assert response.status_code == 422  # Validation error


class TestAuthVerify:
    """Test /api/auth/verify endpoint"""
    
    def test_verify_valid_token(self):
        """Test verifying valid token"""
        # First login to get token
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = login_response.json()["access_token"]
        
        # Verify token
        response = client.get("/api/auth/verify", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") is True or "username" in data
    
    def test_verify_without_token(self):
        """Test verify endpoint without token"""
        response = client.get("/api/auth/verify")
        
        assert response.status_code == 403  # Forbidden or 401


class TestAuthMe:
    """Test /api/auth/me endpoint"""
    
    def test_get_current_user_info(self):
        """Test getting current user information"""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = login_response.json()["access_token"]
        
        # Get user info
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify user data is present
        assert "username" in data or ("data" in data and "username" in data["data"])
    
    def test_get_user_info_without_auth(self):
        """Test getting user info without authentication"""
        response = client.get("/api/auth/me")
        
        assert response.status_code in [401, 403]


class TestAuthLogout:
    """Test /api/auth/logout endpoint"""
    
    def test_logout_success(self):
        """Test successful logout"""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post("/api/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
    
    def test_logout_without_token(self):
        """Test logout without token"""
        response = client.post("/api/auth/logout")
        
        assert response.status_code in [401, 403]


class TestAuthSessions:
    """Test /api/auth/sessions endpoint"""
    
    def test_get_user_sessions(self):
        """Test getting user sessions"""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = login_response.json()["access_token"]
        
        # Get sessions
        response = client.get("/api/auth/sessions", headers={
            "Authorization": f"Bearer {token}"
        })
        
        # Should return 200 with sessions data
        assert response.status_code == 200
        data = response.json()
        
        # Check for sessions in response
        assert "sessions" in data or "data" in data


class TestAuthRefresh:
    """Test /api/auth/refresh endpoint"""
    
    def test_refresh_token_success(self):
        """Test refreshing access token"""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh the token
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return new tokens
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_invalid_token(self):
        """Test refresh with invalid token"""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid_token_string"
        })
        
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test that endpoints are properly protected"""
    
    def test_access_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication"""
        # Try to access a protected endpoint (sync operations require auth)
        response = client.post("/api/sync")
        
        # Should get 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403]
    
    def test_access_protected_endpoint_with_auth(self):
        """Test accessing protected endpoint with valid token"""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = login_response.json()["access_token"]
        
        # Try to access protected endpoint
        response = client.get("/api/employees", headers={
            "Authorization": f"Bearer {token}"
        })
        
        # Should succeed (200) or have other valid status
        # (might be 404 if no data, but not 401/403)
        assert response.status_code not in [401, 403]


class TestRateLimiting:
    """Test rate limiting on auth endpoints"""
    
    @pytest.mark.skip(reason="Rate limiting may interfere with other tests")
    def test_login_rate_limit(self):
        """Test that login endpoint is rate limited"""
        # Make multiple rapid login attempts
        responses = []
        for i in range(10):
            response = client.post("/api/auth/login", json={
                "username": "test",
                "password": "test"
            })
            responses.append(response.status_code)
        
        # At least one should be rate limited (429)
        assert 429 in responses


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
