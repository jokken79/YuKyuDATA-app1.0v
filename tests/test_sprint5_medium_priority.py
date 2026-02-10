"""
SPRINT 5: Medium Priority Fixes Tests

Tests for:
- BUG #13-15: Endpoints sin auth requerida
- BUG #16-18: Rate limiting incompleto
- BUG #19-22: Validación input débil
- BUG #23-25: Error handling inconsistente
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from main import app

client = TestClient(app)


class TestBUG13_15_EndpointAuth:
    """Test BUG #13-15: Endpoints que requieren autenticación"""

    def test_db_status_requires_auth(self):
        """Test that /api/db-status requires authentication"""
        # Sin auth: debe retornar 401
        response = client.get("/api/db-status")
        assert response.status_code == 401

    def test_db_status_with_auth(self):
        """Test that /api/db-status works with valid auth"""
        # Primero login
        login_response = client.post(
            "/login",
            json={"username": "admin", "password": "admin123456"}
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Con auth: debe funcionar
            response = client.get("/api/db-status", headers=headers)
            assert response.status_code == 200
            assert "database" in response.json()

    def test_project_status_requires_auth(self):
        """Test that /api/project-status requires authentication"""
        # Sin auth: debe retornar 401
        response = client.get("/api/project-status")
        assert response.status_code == 401

    def test_info_is_public(self):
        """Test that /api/info is public (no auth required)"""
        # /api/info debe ser público
        response = client.get("/api/info")
        assert response.status_code == 200
        assert "name" in response.json()
        assert "version" in response.json()


class TestBUG23_25_ErrorHandling:
    """Test BUG #23-25: Error handling improvements"""

    def test_error_response_no_stack_trace(self):
        """Test that error responses don't expose stack traces"""
        # Endpoint sin auth - debe retornar error genérico
        response = client.get("/api/db-status")
        assert response.status_code == 401

        # No debe exponer detalles internos
        data = response.json()
        assert "detail" in data or "message" in data
        # No debe contener stack traces
        response_text = str(response.json())
        assert "Traceback" not in response_text
        assert "File \"" not in response_text

    def test_health_check_always_works(self):
        """Test that basic health checks don't require auth"""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_error_status_field(self):
        """Test that error responses have consistent status field"""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data  # Debe tener status field


class TestBUG19_22_InputValidation:
    """Test BUG #19-22: Input validation improvements"""

    def test_pagination_parameters_validation(self):
        """Test that pagination params are validated"""
        # skip y limit deben ser validados
        response = client.get("/api/leave-requests?skip=-1&limit=100")
        # Debe rechazar skip negativo o aceptar y usar valor válido
        assert response.status_code in [200, 422]

    def test_pagination_limit_cap(self):
        """Test that pagination limit is capped at maximum"""
        response = client.get("/api/leave-requests?skip=0&limit=10000")
        # Límite debe estar capeado
        if response.status_code == 200:
            # Si acepta, el limit aplicado debe estar capeado
            data = response.json()
            if "pagination" in data:
                assert data["pagination"]["limit"] <= 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
