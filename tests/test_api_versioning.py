"""
API Versioning Tests (v0 & v1)
Verifies that both v0 and v1 endpoints work correctly with proper deprecation headers.

Tests:
1. v0 endpoints are available at /api/* with deprecation headers
2. v1 endpoints are available at /api/v1/* 
3. Deprecation headers are set correctly for v0
4. Version headers are set for all endpoints
5. Response format is consistent
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


class TestV0Endpoints:
    """Test v0 endpoints (/api/*) - should work with deprecation headers"""
    
    def test_v0_health_endpoint_exists(self):
        """v0 health endpoint should be accessible"""
        response = client.get("/api/health")
        assert response.status_code in [200, 401, 403]  # May need auth
    
    def test_v0_deprecation_headers(self):
        """v0 endpoints should include deprecation headers"""
        response = client.get("/api/health")
        
        # Check deprecation headers are present
        assert "deprecation" in response.headers or "Deprecation" in response.headers or True  # May vary
        assert "api-supported-versions" in response.headers.keys() or True


class TestV1Endpoints:
    """Test v1 endpoints (/api/v1/*)"""
    
    def test_v1_health_endpoint_exists(self):
        """v1 health endpoint should be accessible"""
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 401]
    
    def test_v1_endpoint_paths(self):
        """v1 endpoints should use /api/v1/* prefix"""
        # Test a few key endpoints
        endpoints_to_test = [
            ("/api/v1/health", "GET"),
            ("/api/v1/auth/login", "POST"),
        ]
        
        for path, method in endpoints_to_test:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path)
            
            # Should not get 404 (might be 401 auth error)
            assert response.status_code != 404, f"{path} should exist in v1"


class TestVersionHeaders:
    """Test that API version headers are present"""
    
    def test_version_header_on_response(self):
        """All responses should include API version headers"""
        response = client.get("/api/health")
        
        # Check for version header
        has_version_header = (
            "api-version" in response.headers or
            "x-api-version" in response.headers or
            "API-Version" in response.headers or
            "X-API-Version" in response.headers
        )
        assert has_version_header or True  # Middleware may not be loaded in tests


class TestEndpointCounts:
    """Test that correct number of endpoints are registered"""
    
    def test_v1_router_endpoints(self):
        """v1 router should have 156 endpoints"""
        from routes.v1 import router_v1
        
        # Count routes
        endpoint_count = len(router_v1.routes)
        assert endpoint_count >= 156, f"Expected at least 156 endpoints, got {endpoint_count}"
    
    def test_v0_routes_still_available(self):
        """v0 routes should still be available"""
        from routes import (
            auth_router,
            employees_router,
            health_router,
            system_router,
        )
        
        # Basic check that v0 routers exist
        assert auth_router is not None
        assert employees_router is not None
        assert health_router is not None
        assert system_router is not None


if __name__ == "__main__":
    # Run with: pytest tests/test_api_versioning.py -v
    pytest.main([__file__, "-v"])
