from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.security_headers import SecurityHeadersMiddleware


def _build_client():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get('/ping')
    def ping():
        return {'ok': True}

    return TestClient(app)


def test_security_headers_present():
    client = _build_client()
    response = client.get('/ping')

    assert response.status_code == 200
    assert response.headers.get('x-frame-options') == 'DENY'
    assert response.headers.get('x-content-type-options') == 'nosniff'
    assert 'max-age=' in response.headers.get('strict-transport-security', '')
    assert 'strict-origin-when-cross-origin' in response.headers.get('referrer-policy', '')


def test_csp_and_permissions_policy_present():
    client = _build_client()
    response = client.get('/ping')

    csp = response.headers.get('content-security-policy', '')
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp

    policy = response.headers.get('permissions-policy', '')
    assert 'camera=()' in policy
    assert 'microphone=()' in policy
    assert 'geolocation=()' in policy


from middleware.security_headers import AuthenticationLoggingMiddleware
import logging


def _build_auth_client(status_code=200):
    app = FastAPI()
    app.add_middleware(AuthenticationLoggingMiddleware)

    @app.post('/api/v1/auth/login')
    def login_v1():
        return {'ok': status_code == 200}

    @app.post('/api/auth/login')
    def login_v0():
        return {'ok': status_code == 200}

    return TestClient(app)


def test_auth_logging_handles_v1_login_path(caplog):
    client = _build_auth_client()

    with caplog.at_level(logging.INFO):
        response = client.post('/api/v1/auth/login', json={'username': 'a', 'password': 'b'})

    assert response.status_code == 200
    logs = '\n'.join(record.message for record in caplog.records)
    assert 'AUTH_ATTEMPT login' in logs
    assert 'AUTH_SUCCESS login' in logs


def test_auth_logging_handles_legacy_login_path(caplog):
    client = _build_auth_client()

    with caplog.at_level(logging.INFO):
        response = client.post('/api/auth/login', json={'username': 'a', 'password': 'b'})

    assert response.status_code == 200
    logs = '\n'.join(record.message for record in caplog.records)
    assert 'AUTH_ATTEMPT login' in logs
    assert 'AUTH_SUCCESS login' in logs
