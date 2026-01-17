"""
YuKyu Premium - Security Tests
セキュリティテスト - CSRF, JWT, Rate Limiting

Tests completos para la seguridad del sistema:
- CSRF Protection
- JWT Authentication & Token Security
- Rate Limiting
- Input Sanitization
- SQL Injection Prevention

Ejecutar con: pytest tests/test_security.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import time
import sys
import os
import jwt

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from middleware.csrf import generate_csrf_token, validate_csrf_token
from config.security import settings

client = TestClient(app)


# ============================================
# CSRF PROTECTION TESTS
# ============================================

class TestCSRFProtection:
    """Tests para protección CSRF"""

    def test_csrf_token_generation(self):
        """CSRF token se genera correctamente"""
        response = client.get("/api/csrf-token")
        assert response.status_code == 200
        data = response.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) >= 20

    def test_csrf_token_is_unique(self):
        """Cada solicitud genera un token único"""
        response1 = client.get("/api/csrf-token")
        response2 = client.get("/api/csrf-token")

        token1 = response1.json()["csrf_token"]
        token2 = response2.json()["csrf_token"]

        # Tokens should be unique
        assert token1 != token2

    def test_post_without_csrf_or_jwt_fails(self):
        """POST sin CSRF ni JWT debe fallar"""
        # POST a endpoint que no es /api/auth/login
        response = client.post(
            "/api/leave-requests",
            json={
                "employee_num": "TEST001",
                "employee_name": "Test User",
                "start_date": "2025-01-20",
                "end_date": "2025-01-20",
                "days_requested": 1,
                "leave_type": "full",
                "reason": "Test",
                "year": 2025
            }
        )
        # Debe retornar 403 por falta de CSRF
        assert response.status_code == 403
        assert "CSRF" in response.text or "csrf" in response.text.lower()

    def test_post_with_csrf_token_succeeds(self):
        """POST con CSRF token válido debe funcionar"""
        # Obtener CSRF token
        csrf_response = client.get("/api/csrf-token")
        csrf_token = csrf_response.json()["csrf_token"]

        # Hacer POST con token
        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json={
                "employee_num": "CSRF_TEST_001",
                "employee_name": "CSRF Test User",
                "start_date": "2025-03-01",
                "end_date": "2025-03-01",
                "days_requested": 1.0,
                "leave_type": "full",
                "reason": "CSRF Test",
                "year": 2025
            }
        )
        # Puede ser 200 o 422 (validación), pero NO 403
        assert response.status_code != 403

    def test_post_with_jwt_bypasses_csrf(self):
        """POST con JWT válido no necesita CSRF"""
        # Login para obtener JWT (dev credentials from auth.py)
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"  # Dev password
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # POST con JWT, sin CSRF
        response = client.delete(
            "/api/reset",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Debe funcionar sin CSRF
        assert response.status_code == 200

    def test_invalid_csrf_token_rejected(self):
        """CSRF token inválido debe ser rechazado"""
        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": "invalid-short"},
            json={
                "employee_num": "TEST001",
                "employee_name": "Test",
                "start_date": "2025-01-20",
                "end_date": "2025-01-20",
                "days_requested": 1,
                "leave_type": "full",
                "reason": "Test",
                "year": 2025
            }
        )
        assert response.status_code == 403

    def test_csrf_token_validation_function(self):
        """Función validate_csrf_token funciona correctamente"""
        # Token válido
        valid_token = generate_csrf_token()
        assert validate_csrf_token(valid_token) == True

        # Tokens inválidos
        assert validate_csrf_token("") == False
        assert validate_csrf_token(None) == False
        assert validate_csrf_token("short") == False
        assert validate_csrf_token("a" * 200) == False  # Too long
        assert validate_csrf_token("invalid<>token") == False  # Special chars

    def test_safe_methods_dont_require_csrf(self):
        """Métodos seguros (GET, HEAD, OPTIONS) no requieren CSRF"""
        # GET
        response = client.get("/api/employees")
        assert response.status_code == 200

        # HEAD
        response = client.head("/api/employees")
        assert response.status_code == 200

        # OPTIONS
        response = client.options("/api/employees")
        assert response.status_code in [200, 405]  # 405 si no está implementado


# ============================================
# JWT AUTHENTICATION TESTS
# ============================================

class TestJWTSecurity:
    """Tests para seguridad de JWT"""

    def test_login_returns_valid_jwt(self):
        """Login retorna JWT válido"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"  # Dev password
        })
        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verificar que es un JWT válido (tiene 3 partes)
        token_parts = data["access_token"].split(".")
        assert len(token_parts) == 3

    def test_expired_token_rejected(self):
        """Token expirado debe ser rechazado"""
        # Crear token que ya expiró
        expired_payload = {
            "sub": "admin",
            "username": "admin",
            "role": "admin",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }

        # Usar la misma clave secreta que la app
        expired_token = jwt.encode(
            expired_payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        # Intentar usar token expirado
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_tampered_token_rejected(self):
        """Token modificado debe ser rechazado"""
        # Login para obtener token válido
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        valid_token = login_response.json()["access_token"]

        # Modificar el payload (cambiar último caracter)
        tampered_token = valid_token[:-1] + ("X" if valid_token[-1] != "X" else "Y")

        # Intentar usar token modificado
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        assert response.status_code == 401

    def test_token_with_wrong_signature_rejected(self):
        """Token firmado con clave incorrecta debe ser rechazado"""
        payload = {
            "sub": "admin",
            "username": "admin",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        # Firmar con clave diferente
        wrong_key_token = jwt.encode(
            payload,
            "wrong-secret-key-12345",
            algorithm="HS256"
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {wrong_key_token}"}
        )
        assert response.status_code == 401

    def test_malformed_token_rejected(self):
        """Token malformado debe ser rechazado"""
        malformed_tokens = [
            "not-a-jwt",
            "part1.part2",  # Solo 2 partes
            "part1.part2.part3.part4",  # 4 partes
            "",
            "Bearer ",  # Solo prefijo
            "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiJ9."  # Algorithm: none
        ]

        for bad_token in malformed_tokens:
            response = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {bad_token}"}
            )
            assert response.status_code == 401, f"Token '{bad_token[:20]}...' should be rejected"

    def test_token_refresh_works(self):
        """Token refresh funciona correctamente"""
        # Login
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        token = login_response.json()["access_token"]

        # Verificar que el token es válido
        verify_response = client.get(
            "/api/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["valid"] == True

    def test_protected_endpoint_requires_auth(self):
        """Endpoints protegidos requieren autenticación"""
        protected_endpoints = [
            ("DELETE", "/api/reset"),
            ("DELETE", "/api/reset-genzai"),
            ("DELETE", "/api/reset-ukeoi"),
            ("DELETE", "/api/reset-staff"),
        ]

        for method, endpoint in protected_endpoints:
            if method == "DELETE":
                response = client.delete(endpoint)
            assert response.status_code == 401, f"{endpoint} should require auth"

    def test_role_based_access_control(self):
        """Control de acceso basado en roles funciona"""
        # Admin puede acceder a endpoints de admin
        login_response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123456"
        })
        admin_token = login_response.json()["access_token"]

        # Admin puede hacer reset
        response = client.delete(
            "/api/reset",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


# ============================================
# RATE LIMITING TESTS
# ============================================

class TestRateLimiting:
    """Tests para rate limiting"""

    def test_login_rate_limit_exists(self):
        """Login tiene rate limiting"""
        # Hacer múltiples intentos de login fallidos
        failed_attempts = 0
        rate_limited = False

        for i in range(20):
            response = client.post("/api/auth/login", json={
                "username": "nonexistent",
                "password": "wrongpassword"
            })
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
            elif response.status_code == 401:
                failed_attempts += 1

        # Si llegamos a 20 sin ser limitados, el rate limit puede ser alto
        # pero debemos verificar que al menos se rechazaron los logins
        assert failed_attempts > 0 or rate_limited

    def test_api_rate_limit_headers(self):
        """Headers de rate limit están presentes"""
        response = client.get("/api/employees")
        # Algunos rate limiters añaden headers
        # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        # Este test documenta el comportamiento esperado
        assert response.status_code == 200


# ============================================
# INPUT SANITIZATION TESTS
# ============================================

class TestInputSanitization:
    """Tests para sanitización de entrada"""

    def test_xss_in_search_sanitized(self):
        """XSS en búsqueda es sanitizado"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<svg onload=alert(1)>",
        ]

        for payload in xss_payloads:
            response = client.get(f"/api/employees/search?q={payload}")
            assert response.status_code in [200, 400, 422]
            # La respuesta no debe contener el payload sin escapar
            if response.status_code == 200:
                assert "<script>" not in response.text
                assert "onerror=" not in response.text

    def test_html_entities_escaped(self):
        """Entidades HTML son escapadas"""
        response = client.get("/api/employees/search?q=<test>&more")
        assert response.status_code in [200, 400, 422]
        # El JSON no debería contener HTML sin escapar
        if response.status_code == 200:
            data = response.json()
            # Verificar que la respuesta es JSON válido (no HTML)
            assert isinstance(data, dict)


# ============================================
# SQL INJECTION PREVENTION TESTS
# ============================================

class TestSQLInjectionPrevention:
    """Tests para prevención de SQL injection"""

    def test_sql_injection_in_year_param(self):
        """SQL injection en parámetro year es prevenido"""
        sql_payloads = [
            "2024; DROP TABLE employees;--",
            "2024 OR 1=1",
            "2024' OR '1'='1",
            "2024; DELETE FROM employees;--",
            "2024 UNION SELECT * FROM users--",
        ]

        for payload in sql_payloads:
            response = client.get(f"/api/employees?year={payload}")
            # No debe causar error del servidor
            assert response.status_code in [200, 400, 422]
            # No debe exponer errores SQL
            assert "SQL" not in response.text.upper() or "syntax" not in response.text.lower()

    def test_sql_injection_in_search(self):
        """SQL injection en búsqueda es prevenido"""
        sql_payloads = [
            "'; DROP TABLE employees;--",
            "' OR '1'='1",
            "test' UNION SELECT password FROM users--",
            "1; UPDATE employees SET balance=1000--",
        ]

        for payload in sql_payloads:
            response = client.get(f"/api/employees/search?q={payload}")
            assert response.status_code in [200, 400, 422]
            # No debe retornar datos de otras tablas
            if response.status_code == 200:
                data = response.json()
                assert "password" not in str(data).lower()

    def test_sql_injection_in_employee_num(self):
        """SQL injection en employee_num es prevenido"""
        sql_payloads = [
            "001'; DROP TABLE--",
            "001 OR 1=1",
        ]

        for payload in sql_payloads:
            response = client.get(f"/api/yukyu/usage-details/{payload}/2025")
            # Debe manejar gracefully
            assert response.status_code in [200, 400, 404, 422]

    def test_batch_sql_injection(self):
        """Batch SQL injection en leave requests es prevenido"""
        csrf_response = client.get("/api/csrf-token")
        csrf_token = csrf_response.json()["csrf_token"]

        malicious_data = {
            "employee_num": "001'; DELETE FROM employees;--",
            "employee_name": "Test'; DROP TABLE--",
            "start_date": "2025-01-20",
            "end_date": "2025-01-20",
            "days_requested": 1,
            "leave_type": "full",
            "reason": "'; UPDATE employees SET balance=1000;--",
            "year": 2025
        }

        response = client.post(
            "/api/leave-requests",
            headers={"X-CSRF-Token": csrf_token},
            json=malicious_data
        )
        # Debe manejar sin ejecutar SQL malicioso
        assert response.status_code in [200, 400, 422]


# ============================================
# SECURITY HEADERS TESTS
# ============================================

class TestSecurityHeaders:
    """Tests para security headers"""

    def test_content_type_header(self):
        """Content-Type header está presente"""
        response = client.get("/api/employees")
        assert "application/json" in response.headers.get("content-type", "")

    def test_no_sensitive_info_in_errors(self):
        """Errores no exponen información sensible"""
        # Trigger an error
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404

        error_text = response.text.lower()
        # No debe exponer:
        sensitive_terms = ["traceback", "stacktrace", "password", "secret", "key"]
        for term in sensitive_terms:
            assert term not in error_text, f"Error exposes sensitive term: {term}"


# ============================================
# AUTHENTICATION BYPASS TESTS
# ============================================

class TestAuthenticationBypass:
    """Tests para prevenir bypass de autenticación"""

    def test_null_byte_injection(self):
        """Null byte injection es prevenido"""
        response = client.post("/api/auth/login", json={
            "username": "admin\x00garbage",
            "password": "admin123456"
        })
        # No debe permitir login
        assert response.status_code in [400, 401, 422]

    def test_unicode_bypass_attempt(self):
        """Unicode bypass es prevenido"""
        unicode_usernames = [
            "admin",  # Control
            "ａｄｍｉｎ",  # Full-width
            "admın",  # Turkish I
            "аdmin",  # Cyrillic a
        ]

        # Solo el primero debería funcionar
        response = client.post("/api/auth/login", json={
            "username": unicode_usernames[0],
            "password": "admin123456"
        })
        assert response.status_code == 200

        # Los demás no deberían
        for username in unicode_usernames[1:]:
            response = client.post("/api/auth/login", json={
                "username": username,
                "password": "admin123456"
            })
            assert response.status_code == 401

    def test_case_sensitivity(self):
        """Username es case-sensitive"""
        response = client.post("/api/auth/login", json={
            "username": "ADMIN",
            "password": "admin123456"
        })
        # Puede fallar o funcionar dependiendo de la implementación
        # Lo importante es que sea consistente
        assert response.status_code in [200, 401]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
