"""
Tests for the global exception handler middleware.

Tests cover:
- Unhandled exceptions (500 errors)
- HTTP exceptions (4xx/5xx errors)
- Validation errors (422 errors)
- Request ID tracking
- Response format consistency
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError

# Import from middleware directly (avoid __init__.py dependencies)
import sys
from pathlib import Path
middleware_path = str(Path(__file__).parent.parent / "middleware")
sys.path.insert(0, middleware_path)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct import from the exception_handler module file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "exception_handler",
    Path(__file__).parent.parent / "middleware" / "exception_handler.py"
)
exception_handler_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exception_handler_module)

global_exception_handler = exception_handler_module.global_exception_handler
http_exception_handler = exception_handler_module.http_exception_handler
validation_exception_handler = exception_handler_module.validation_exception_handler
pydantic_validation_handler = exception_handler_module.pydantic_validation_handler
register_exception_handlers = exception_handler_module.register_exception_handlers
generate_request_id = exception_handler_module.generate_request_id
create_error_response = exception_handler_module.create_error_response
get_request_context = exception_handler_module.get_request_context
_sanitize_input = exception_handler_module._sanitize_input


class TestGenerateRequestId:
    """Tests for request ID generation."""

    def test_generates_string(self):
        """Request ID should be a string."""
        request_id = generate_request_id()
        assert isinstance(request_id, str)

    def test_generates_8_chars(self):
        """Request ID should be 8 characters."""
        request_id = generate_request_id()
        assert len(request_id) == 8

    def test_generates_unique_ids(self):
        """Each call should generate a unique ID."""
        ids = [generate_request_id() for _ in range(100)]
        # All should be unique
        assert len(set(ids)) == 100


class TestCreateErrorResponse:
    """Tests for error response creation."""

    def test_basic_error_response(self):
        """Test basic error response format."""
        response = create_error_response(
            status_code=500,
            error="Internal server error",
            message="Something went wrong",
            request_id="abc12345"
        )

        assert response["success"] is False
        assert response["status"] == "error"
        assert response["error"] == "Internal server error"
        assert response["message"] == "Something went wrong"
        assert response["request_id"] == "abc12345"
        assert "timestamp" in response

    def test_error_response_with_details(self):
        """Test error response with additional details."""
        details = [{"field": "name", "message": "Required"}]
        response = create_error_response(
            status_code=422,
            error="Validation error",
            message="Validation failed",
            request_id="xyz98765",
            details=details
        )

        assert response["details"] == details

    def test_error_response_without_details(self):
        """Test that details key is not present when not provided."""
        response = create_error_response(
            status_code=400,
            error="Bad request",
            message="Invalid input",
            request_id="test1234"
        )

        assert "details" not in response


class TestSanitizeInput:
    """Tests for input sanitization."""

    def test_sanitize_none(self):
        """None should return None."""
        assert _sanitize_input(None) is None

    def test_sanitize_short_string(self):
        """Short strings should be returned as-is."""
        assert _sanitize_input("hello") == "hello"

    def test_sanitize_long_string(self):
        """Long strings should be truncated."""
        long_string = "x" * 200
        result = _sanitize_input(long_string)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")

    def test_sanitize_sensitive_password(self):
        """Password-like values should be redacted."""
        assert _sanitize_input("password123") == "[REDACTED]"
        assert _sanitize_input("my_secret_key") == "[REDACTED]"
        assert _sanitize_input("auth_token") == "[REDACTED]"

    def test_sanitize_numbers(self):
        """Numbers should be returned as-is."""
        assert _sanitize_input(42) == 42
        assert _sanitize_input(3.14) == 3.14

    def test_sanitize_bool(self):
        """Booleans should be returned as-is."""
        assert _sanitize_input(True) is True
        assert _sanitize_input(False) is False

    def test_sanitize_list(self):
        """Lists should show summary."""
        result = _sanitize_input([1, 2, 3])
        assert "<list with 3 items>" == result

    def test_sanitize_dict(self):
        """Dicts should show summary."""
        result = _sanitize_input({"a": 1, "b": 2})
        assert "<dict with 2 items>" == result


class TestExceptionHandlerIntegration:
    """Integration tests using a test FastAPI app."""

    @pytest.fixture
    def test_app(self):
        """Create a test app with exception handlers."""
        app = FastAPI()
        register_exception_handlers(app)

        class TestModel(BaseModel):
            name: str = Field(..., min_length=2)
            age: int = Field(..., ge=0, le=150)

        @app.get("/test/ok")
        async def test_ok():
            return {"status": "ok"}

        @app.get("/test/http-error")
        async def test_http_error():
            raise HTTPException(status_code=404, detail="Resource not found")

        @app.get("/test/server-error")
        async def test_server_error():
            raise RuntimeError("Unexpected error")

        @app.get("/test/forbidden")
        async def test_forbidden():
            raise HTTPException(status_code=403, detail="Access denied")

        @app.post("/test/validation")
        async def test_validation(data: TestModel):
            return {"received": data.dict()}

        @app.get("/test/bad-request")
        async def test_bad_request():
            raise HTTPException(status_code=400, detail="Invalid parameters")

        return TestClient(app, raise_server_exceptions=False)

    def test_successful_request(self, test_app):
        """Successful requests should not be affected."""
        response = test_app.get("/test/ok")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_http_404_error(self, test_app):
        """HTTP 404 should return standardized response."""
        response = test_app.get("/test/http-error")
        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False
        assert data["status"] == "error"
        assert data["error"] == "Not found"
        assert "Resource not found" in data["message"]
        assert "request_id" in data
        assert "X-Request-ID" in response.headers

    def test_http_403_error(self, test_app):
        """HTTP 403 should return standardized response."""
        response = test_app.get("/test/forbidden")
        assert response.status_code == 403

        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Forbidden"
        assert "Access denied" in data["message"]

    def test_http_400_error(self, test_app):
        """HTTP 400 should return standardized response."""
        response = test_app.get("/test/bad-request")
        assert response.status_code == 400

        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Bad request"

    def test_server_error(self, test_app):
        """Unhandled exceptions should return 500 with safe message."""
        response = test_app.get("/test/server-error")
        assert response.status_code == 500

        data = response.json()
        assert data["success"] is False
        assert data["status"] == "error"
        assert data["error"] == "Internal server error"
        # Should not leak the actual error message
        assert "Unexpected error" not in data["message"]
        assert "request_id" in data
        assert "X-Request-ID" in response.headers

    def test_validation_error_missing_field(self, test_app):
        """Missing required field should return 422."""
        response = test_app.post("/test/validation", json={"age": 25})
        assert response.status_code == 422

        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Validation error"
        assert "details" in data
        # Should indicate which field failed
        fields = [d["field"] for d in data["details"]]
        assert any("name" in f for f in fields)

    def test_validation_error_invalid_type(self, test_app):
        """Invalid type should return 422."""
        response = test_app.post("/test/validation", json={"name": "John", "age": "not_a_number"})
        assert response.status_code == 422

        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Validation error"
        assert "details" in data

    def test_validation_error_constraint_violation(self, test_app):
        """Constraint violation should return 422."""
        response = test_app.post("/test/validation", json={"name": "J", "age": 25})  # name too short
        assert response.status_code == 422

        data = response.json()
        assert "details" in data
        fields = [d["field"] for d in data["details"]]
        assert any("name" in f for f in fields)

    def test_request_id_header(self, test_app):
        """All error responses should include X-Request-ID header."""
        # Test 404
        response = test_app.get("/test/http-error")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 8

        # Test 500
        response = test_app.get("/test/server-error")
        assert "X-Request-ID" in response.headers

        # Test 422
        response = test_app.post("/test/validation", json={})
        assert "X-Request-ID" in response.headers

    def test_request_id_matches_body(self, test_app):
        """Request ID in header should match body."""
        response = test_app.get("/test/http-error")
        header_id = response.headers["X-Request-ID"]
        body_id = response.json()["request_id"]
        assert header_id == body_id


@pytest.mark.skipif(
    True,  # Skip by default - can be enabled when all dependencies are installed
    reason="Requires full app dependencies (jwt, cryptography, etc.)"
)
class TestRealAppIntegration:
    """Tests using the actual YuKyuDATA app.

    These tests require the full application to be importable, including
    all dependencies like jwt, cryptography, etc. They are skipped by default
    in environments where these are not available.

    To run these tests, ensure all requirements.txt dependencies are installed.
    """

    @pytest.fixture
    def client(self):
        """Create test client for the actual app."""
        from main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_404_on_unknown_endpoint(self, client):
        """Unknown endpoint should return formatted 404."""
        response = client.get("/api/nonexistent/endpoint/12345")
        assert response.status_code == 404

        data = response.json()
        assert data["success"] is False
        assert "request_id" in data

    def test_validation_error_format(self, client):
        """Validation errors should have consistent format."""
        # Try to create a leave request with invalid data
        response = client.post("/api/leave-requests", json={
            "employee_num": "",  # Invalid - empty
            "start_date": "invalid-date",
            "end_date": "also-invalid",
            "days_requested": -5  # Invalid - negative
        })

        # Should be 422 for validation or possibly other error
        assert response.status_code in [400, 401, 403, 422]

        data = response.json()
        assert data["success"] is False
        assert "request_id" in data or "error" in data

    def test_error_response_timestamp(self, client):
        """Error responses should include timestamp."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

        data = response.json()
        if "timestamp" in data:
            # Timestamp should be ISO format
            assert "T" in data["timestamp"]
            assert data["timestamp"].endswith("Z")


class TestGetRequestContext:
    """Tests for request context extraction."""

    def test_extract_basic_context(self):
        """Test basic context extraction from mock request."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.query_params = None
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get = lambda key, default="": {
            "X-Forwarded-For": None,
            "User-Agent": "TestAgent/1.0"
        }.get(key, default)

        context = get_request_context(mock_request)

        assert context["method"] == "GET"
        assert context["path"] == "/api/test"
        assert context["client_ip"] == "127.0.0.1"
        assert context["user_agent"] == "TestAgent/1.0"

    def test_extract_forwarded_ip(self):
        """Test extraction of forwarded IP from proxy headers."""
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.url.path = "/api/data"
        mock_request.query_params = None
        mock_request.client.host = "10.0.0.1"  # Internal proxy IP
        mock_request.headers.get = lambda key, default="": {
            "X-Forwarded-For": "203.0.113.50, 70.41.3.18",
            "User-Agent": "Browser/1.0"
        }.get(key, default)

        context = get_request_context(mock_request)

        # Should use first IP from X-Forwarded-For
        assert context["client_ip"] == "203.0.113.50"

    def test_truncate_long_user_agent(self):
        """Long user agent should be truncated."""
        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.query_params = None
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get = lambda key, default="": {
            "User-Agent": "A" * 500  # Very long user agent
        }.get(key, default)

        context = get_request_context(mock_request)

        assert len(context["user_agent"]) == 200
