import hashlib
import os

import pytest
from fastapi.testclient import TestClient


def _derive(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()


# Configure mandatory auth environment for tests
TEST_SALT = os.environ.get("ADMIN_PASSWORD_SALT", "test-salt")
os.environ.setdefault("ADMIN_PASSWORD_SALT", TEST_SALT)
os.environ.setdefault("ADMIN_PASSWORD_HASH", _derive("admin123", TEST_SALT))
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_NAME", "Administrator")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": os.environ["ADMIN_USERNAME"], "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def auth_headers(admin_token: str):
    return {"Authorization": f"Bearer {admin_token}"}
