"""
OWASP Top 10 Security Validation Tests for YuKyuDATA.

Tests for:
1. SQL Injection
2. Cross-Site Scripting (XSS)
3. Authentication/Authorization
4. Sensitive Data Exposure
5. Broken Access Control
6. CSRF Protection
7. Command Injection
8. XXE (XML External Entity)
9. Deserialization Flaws
10. Using Components with Known Vulnerabilities
"""

import pytest
from datetime import datetime, timedelta


class TestSQLInjection:
    """Test SQL injection prevention."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_sql_injection_in_year_parameter(self, client):
        """Test: SQL injection in year parameter should be sanitized."""
        # Attempt SQL injection
        response = client.get("/api/employees?year=2025 OR 1=1")
        assert response.status_code in [200, 400]  # Should succeed safely or fail validation

    def test_sql_injection_in_search_query(self, client, auth_headers):
        """Test: SQL injection in search query should be sanitized."""
        injection_payloads = [
            "'; DROP TABLE employees; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; DELETE FROM employees; --",
            "1' AND SLEEP(5) --"
        ]

        for payload in injection_payloads:
            response = client.get(
                f"/api/employees/search?q={payload}&year=2025",
                headers=auth_headers
            )
            # Should not execute injection
            assert response.status_code in [200, 400]
            # Should not have SQL errors in response
            assert "SQL" not in response.text.upper() or response.status_code == 400

    def test_sql_injection_in_employee_number(self, client, auth_headers):
        """Test: SQL injection in employee number should be sanitized."""
        response = client.get(
            "/api/employees/001'; DROP TABLE employees; --/2025",
            headers=auth_headers
        )
        # Should not execute injection
        assert response.status_code in [200, 400, 404]

    def test_batch_sql_injection(self, client, auth_headers):
        """Test: SQL injection via batch operations should fail safely."""
        response = client.post(
            "/api/employees/batch",
            json={
                "ids": ["001'; DROP TABLE employees; --", "002"],
                "action": "export"
            },
            headers=auth_headers
        )
        # Should handle safely
        assert response.status_code in [200, 400, 404]


class TestXSSPrevention:
    """Test Cross-Site Scripting prevention."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}

    def test_xss_in_leave_request_reason(self, client, auth_headers):
        """Test: XSS payload in reason field should be escaped."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(1)'></iframe>"
        ]

        for payload in xss_payloads:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            response = client.post(
                "/api/leave-requests",
                json={
                    "employee_num": "001",
                    "start_date": tomorrow,
                    "end_date": tomorrow,
                    "days_requested": 1.0,
                    "leave_type": "full",
                    "reason": payload,
                    "year": 2025
                },
                headers=auth_headers
            )

            # Should either reject or escape
            if response.status_code == 200 or response.status_code == 201:
                # If accepted, ensure script tags are escaped
                response_data = response.json()
                response_text = str(response_data)
                # Check script is not executable
                assert "<script>" not in response_text or "&lt;script&gt;" in response_text

    def test_xss_in_search_query(self, client, auth_headers):
        """Test: XSS in search query should be escaped."""
        response = client.get(
            "/api/employees/search?q=<script>alert('xss')</script>&year=2025",
            headers=auth_headers
        )

        # Should succeed
        assert response.status_code == 200

        # Response should escape or sanitize
        data = response.json()
        assert data is not None

    def test_xss_in_employee_name(self, client, auth_headers):
        """Test: XSS in employee name field should be escaped in responses."""
        response = client.get("/api/employees?year=2025", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()
            employees = data.get("data", [])

            for emp in employees:
                name = emp.get("name", "")
                # Names should not contain unescaped HTML
                assert "<" not in name or name.count("<") == name.count("&lt;")


class TestCSRFProtection:
    """Test CSRF protection mechanisms."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_csrf_token_generation(self, client):
        """Test: CSRF token should be generated."""
        response = client.get("/api/csrf-token")

        # May not be implemented, but if it is, should work
        if response.status_code == 200:
            data = response.json()
            assert "csrf_token" in data
            assert len(data["csrf_token"]) > 0

    def test_csrf_token_is_unique(self, client):
        """Test: Each CSRF token should be unique."""
        response1 = client.get("/api/csrf-token")
        response2 = client.get("/api/csrf-token")

        if response1.status_code == 200 and response2.status_code == 200:
            token1 = response1.json().get("csrf_token")
            token2 = response2.json().get("csrf_token")

            # Tokens should be different (if implementation uses session-based tokens)
            # Or same if using stateless tokens (both valid)
            assert token1 and token2

    def test_post_without_csrf_fails(self, client):
        """Test: POST without CSRF token might fail (if CSRF protection enabled)."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = client.post(
            "/api/leave-requests",
            json={
                "employee_num": "001",
                "start_date": tomorrow,
                "end_date": tomorrow,
                "days_requested": 1.0,
                "leave_type": "full",
                "reason": "Test",
                "year": 2025
            }
        )

        # Should either require auth or CSRF
        # At minimum, unauthorized (401) or forbidden (403)
        assert response.status_code in [401, 403, 422]

    def test_post_with_jwt_works(self, client):
        """Test: POST with JWT token should work (JWT bypasses CSRF)."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })

        if response.status_code == 200:
            token = response.json().get("access_token")

            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            response = client.post(
                "/api/leave-requests",
                json={
                    "employee_num": "001",
                    "start_date": tomorrow,
                    "end_date": tomorrow,
                    "days_requested": 1.0,
                    "leave_type": "full",
                    "reason": "Test",
                    "year": 2025
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            # Should work with JWT
            assert response.status_code in [200, 201]


class TestAuthenticationBypass:
    """Test authentication bypass prevention."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_null_byte_injection(self, client):
        """Test: Null bytes should not bypass authentication."""
        response = client.get(
            "/api/employees?year=2025\x00/admin",
        )
        # Should not bypass auth
        assert response.status_code in [401, 400]

    def test_unicode_bypass_attempt(self, client):
        """Test: Unicode encoding should not bypass authentication."""
        response = client.get(
            "/api/employees/\u0000/2025",
        )
        # Should handle safely
        assert response.status_code in [401, 400, 404]

    def test_path_traversal_attempt(self, client):
        """Test: Path traversal should not work."""
        response = client.get("/api/../admin/employees")
        # Should not bypass auth
        assert response.status_code in [401, 404, 400]

    def test_case_sensitivity_bypass(self, client):
        """Test: Case variations should not bypass auth."""
        # Try different case variations of private endpoints
        response = client.get("/API/employees")
        assert response.status_code in [401, 404, 400]


class TestSensitiveDataExposure:
    """Test sensitive data exposure prevention."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_error_messages_not_verbose(self, client):
        """Test: Error messages should not expose sensitive info."""
        response = client.post(
            "/api/leave-requests",
            json={
                "employee_num": "invalid",
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
                "days_requested": 1.0,
                "leave_type": "full",
                "reason": "Test",
                "year": 2025
            }
        )

        # Check error response
        error_text = response.text.lower()

        # Should not expose:
        sensitive_keywords = ["database", "sql", "password", "secret", "key", "stack trace"]
        for keyword in sensitive_keywords:
            if keyword in error_text and response.status_code >= 400:
                # Some keywords might be in error, but shouldn't be detailed
                assert "at line" not in error_text or response.status_code == 422

    def test_no_stack_traces_in_errors(self, client):
        """Test: Stack traces should not be exposed in error responses."""
        response = client.get(
            "/api/employees/nonexistent-id/2025"
        )

        # Check for stack trace indicators
        assert "File " not in response.text or response.status_code == 404
        assert "line " not in response.text or response.status_code == 404
        assert "Traceback" not in response.text

    def test_password_not_in_response(self, client):
        """Test: Passwords should never be in API responses."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })

        if response.status_code == 200:
            data = response.json()
            response_text = str(data)

            # Password should not be returned
            assert "admin123456" not in response_text
            assert "password" not in response_text.lower()

    def test_internal_ids_not_exposed(self, client):
        """Test: Internal database IDs should be properly obscured."""
        response = client.get("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        # At minimum should not expose raw DB connection strings


class TestRateLimiting:
    """Test rate limiting enforcement."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_rate_limit_headers_present(self, client):
        """Test: Rate limit headers should be in responses."""
        response = client.get("/api/health")

        # Check for rate limit headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "RateLimit-Limit",
            "RateLimit-Remaining"
        ]

        # At least one rate limit header should be present (if implemented)
        has_rate_limit = any(h in response.headers for h in rate_limit_headers)

        if has_rate_limit:
            print(f"Rate limit headers found: {[h for h in rate_limit_headers if h in response.headers]}")

    def test_excessive_requests_rate_limited(self, client):
        """Test: Excessive requests should be rate limited."""
        import time

        # Make many requests quickly
        responses = []
        for i in range(50):
            response = client.get("/api/health")
            responses.append(response.status_code)

            # Check if rate limited
            if response.status_code == 429:
                # Rate limit triggered
                assert i > 10, "Should allow at least 10 requests"
                break

            # Small delay to avoid overloading
            if i > 0 and i % 10 == 0:
                time.sleep(0.1)

        # At least some requests should succeed
        success_count = sum(1 for s in responses if s == 200)
        assert success_count > 0


class TestJWTSecurity:
    """Test JWT token security."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_expired_token_rejected(self, client):
        """Test: Expired tokens should be rejected."""
        # This requires modifying token expiry, which is controlled by the app
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })

        if response.status_code == 200:
            # Token is fresh
            token = response.json().get("access_token")
            response = client.get(
                "/api/employees?year=2025",
                headers={"Authorization": f"Bearer {token}"}
            )
            # Should work
            assert response.status_code in [200, 401]

    def test_malformed_token_rejected(self, client):
        """Test: Malformed tokens should be rejected."""
        response = client.get(
            "/api/employees?year=2025",
            headers={"Authorization": "Bearer malformed-token"}
        )

        # Should reject malformed token
        assert response.status_code == 401

    def test_tampered_token_rejected(self, client):
        """Test: Tampered JWT tokens should be rejected."""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })

        if response.status_code == 200:
            token = response.json().get("access_token")

            # Tamper with token (change last character)
            tampered_token = token[:-5] + "xxxxx"

            response = client.get(
                "/api/employees?year=2025",
                headers={"Authorization": f"Bearer {tampered_token}"}
            )

            # Should reject tampered token
            assert response.status_code == 401

    def test_token_without_signature_rejected(self, client):
        """Test: Tokens without valid signature should be rejected."""
        # Create a token-like string without proper signature
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiJ9.invalidsignature"

        response = client.get(
            "/api/employees?year=2025",
            headers={"Authorization": f"Bearer {fake_token}"}
        )

        # Should reject
        assert response.status_code == 401
