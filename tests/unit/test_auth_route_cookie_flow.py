from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.v1.auth import router


def _build_client(monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix='/api/v1')

    # Disable rate limiter dependency effects by making it no-op dependency return True
    monkeypatch.setattr('routes.v1.auth.rate_limiter_strict', lambda: True)

    return TestClient(app)


def test_login_sets_access_token_cookie(monkeypatch):
    client = _build_client(monkeypatch)

    class _TokenPair:
        access_token = 'access123'
        refresh_token = 'refresh123'
        token_type = 'bearer'
        expires_in = 900

    monkeypatch.setattr('routes.v1.auth.auth_service.authenticate_user', lambda u, p: {'username': u})
    monkeypatch.setattr('routes.v1.auth.auth_service.create_token_pair', lambda *args, **kwargs: _TokenPair())

    response = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'admin123456'})

    assert response.status_code == 200
    assert response.cookies.get('access_token') == 'access123'


def test_verify_accepts_cookie_token(monkeypatch):
    client = _build_client(monkeypatch)

    monkeypatch.setattr('routes.v1.auth.auth_service.verify_access_token', lambda t: {'sub': 'admin', 'exp': 999999, 'type': 'access'})

    response = client.get('/api/v1/auth/verify', cookies={'access_token': 'cookie-token'})

    assert response.status_code == 200
    payload = response.json().get('data', {})
    assert payload.get('valid') is True
    assert payload.get('username') == 'admin'


def test_logout_revokes_cookie_token_and_clears_cookie(monkeypatch):
    client = _build_client(monkeypatch)

    called = {'revoked': None}

    def _revoke(token):
        called['revoked'] = token

    monkeypatch.setattr('routes.v1.auth.auth_service.revoke_token', _revoke)

    response = client.post('/api/v1/auth/logout', cookies={'access_token': 'cookie-token'})

    assert response.status_code == 200
    assert called['revoked'] == 'cookie-token'
    set_cookie = response.headers.get('set-cookie', '')
    assert 'access_token=' in set_cookie


def test_verify_without_token_returns_401():
    app = FastAPI()
    app.include_router(router, prefix='/api/v1')
    client = TestClient(app)

    response = client.get('/api/v1/auth/verify')

    assert response.status_code == 401


def test_refresh_sets_access_token_cookie(monkeypatch):
    client = _build_client(monkeypatch)

    class _TokenPair:
        access_token = 'new-access-123'
        refresh_token = 'new-refresh-123'
        token_type = 'bearer'
        expires_in = 900

    monkeypatch.setattr('routes.v1.auth.auth_service.refresh_access_token', lambda *args, **kwargs: _TokenPair())

    response = client.post('/api/v1/auth/refresh', json={'refresh_token': 'old-refresh'})

    assert response.status_code == 200
    assert response.cookies.get('access_token') == 'new-access-123'
