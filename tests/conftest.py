"""
Shared pytest fixtures and configuration for YuKyuDATA tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set testing environment BEFORE importing app modules
os.environ["TESTING"] = "true"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["DEBUG"] = "true"  # Enable dev users

# Test credentials (match auth.py dev fallback)
TEST_ADMIN_USERNAME = "admin"
TEST_ADMIN_PASSWORD = "admin123456"  # Dev password from auth.py
TEST_USER_USERNAME = "demo"
TEST_USER_PASSWORD = "demo123456"


def _reset_all_rate_limiters():
    """Helper to reset all rate limiters in the app."""
    from collections import defaultdict

    try:
        from main import rate_limiter
        if hasattr(rate_limiter, 'reset'):
            rate_limiter.reset()
        elif hasattr(rate_limiter, 'requests'):
            # Use clear() to maintain defaultdict behavior
            if hasattr(rate_limiter.requests, 'clear'):
                rate_limiter.requests.clear()
            else:
                rate_limiter.requests = defaultdict(list)
    except (ImportError, AttributeError):
        pass

    try:
        # Try direct import to avoid middleware/__init__.py dependency chain
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'rate_limiter_reset',
            str(Path(__file__).parent.parent / 'middleware' / 'rate_limiter.py')
        )
        rate_limiter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rate_limiter_module)

        rate_limiter_strict = rate_limiter_module.rate_limiter_strict
        rate_limiter_normal = rate_limiter_module.rate_limiter_normal
        rate_limiter_relaxed = rate_limiter_module.rate_limiter_relaxed
        user_aware_limiter = rate_limiter_module.user_aware_limiter

        # Reset legacy rate limiters
        for rl in [rate_limiter_strict, rate_limiter_normal, rate_limiter_relaxed]:
            if hasattr(rl, 'reset'):
                rl.reset()
            elif hasattr(rl, 'requests'):
                if hasattr(rl.requests, 'clear'):
                    rl.requests.clear()
        # Reset new user-aware limiter
        if hasattr(user_aware_limiter, 'reset'):
            user_aware_limiter.reset()
    except Exception:
        # Fallback: try package import
        try:
            from middleware.rate_limiter import (
                rate_limiter_strict,
                rate_limiter_normal,
                rate_limiter_relaxed,
                user_aware_limiter
            )
            for rl in [rate_limiter_strict, rate_limiter_normal, rate_limiter_relaxed]:
                if hasattr(rl, 'reset'):
                    rl.reset()
            if hasattr(user_aware_limiter, 'reset'):
                user_aware_limiter.reset()
        except (ImportError, AttributeError):
            pass


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiting():
    """Disable rate limiting for all tests."""
    _reset_all_rate_limiters()
    yield
    # Cleanup after all tests
    os.environ.pop("TESTING", None)
    os.environ.pop("RATE_LIMIT_ENABLED", None)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test automatically."""
    _reset_all_rate_limiters()
    yield
    _reset_all_rate_limiters()


@pytest.fixture(scope="session")
def database_type():
    """Get configured database type (sqlite or postgresql)."""
    return os.getenv('DATABASE_TYPE', 'sqlite').lower()


@pytest.fixture(scope="session")
def database_url():
    """Get configured database URL."""
    return os.getenv('DATABASE_URL', 'sqlite:///./test.db')


@pytest.fixture
def sample_employee_data():
    """Sample employee data fixture."""
    return {
        'id': 'TEST_EMP_001_2025',
        'employeeNum': 'TEST_EMP_001',
        'name': '試験太郎',
        'haken': 'テスト工場',
        'granted': 20.0,
        'used': 5.0,
        'balance': 15.0,
        'expired': 0.0,
        'usageRate': 25.0,
        'year': 2025
    }


@pytest.fixture
def sample_genzai_data():
    """Sample Genzai (dispatch employee) data fixture."""
    return {
        'id': 'genzai_TEST_001',
        'status': '在職中',
        'employee_num': 'TEST_EMP_001',
        'dispatch_id': 'D_TEST',
        'dispatch_name': 'テスト派遣先',
        'department': 'テスト部',
        'line': 'テストライン',
        'job_content': 'テスト作業',
        'name': '試験太郎',
        'kana': 'シケンタロウ',
        'gender': '男',
        'nationality': '日本',
        'birth_date': '1995-06-20',
        'age': 29,
        'hourly_wage': 1200,
        'wage_revision': '2025-01-01',
        'hire_date': '2021-04-01',
        'leave_date': None
    }


@pytest.fixture
def sample_ukeoi_data():
    """Sample Ukeoi (contract employee) data fixture."""
    return {
        'id': 'ukeoi_TEST_001',
        'status': '在職中',
        'employee_num': 'TEST_EMP_002',
        'contract_business': 'テスト事業',
        'name': '試験花子',
        'kana': 'シケンハナコ',
        'gender': '女',
        'nationality': '日本',
        'birth_date': '1992-03-10',
        'age': 32,
        'hourly_wage': 1400,
        'wage_revision': '2025-01-01',
        'hire_date': '2019-07-01',
        'leave_date': None
    }


@pytest.fixture
def sample_staff_data():
    """Sample Staff data fixture."""
    return {
        'id': 'staff_TEST_001',
        'status': '在職中',
        'employee_num': 'TEST_EMP_003',
        'office': '本社',
        'name': '試験次郎',
        'kana': 'シケンジロウ',
        'gender': '男',
        'nationality': '日本',
        'birth_date': '1988-12-25',
        'age': 36,
        'visa_expiry': '2030-12-24',
        'visa_type': '就労ビザ',
        'spouse': '試験妻子',
        'postal_code': '100-0001',
        'address': '東京都千代田区丸の内',
        'building': 'テストビル1階',
        'hire_date': '2015-04-01',
        'leave_date': None
    }


@pytest.fixture
def sample_usage_details_data():
    """Sample usage details data fixture."""
    return [
        {
            'employee_num': 'TEST_EMP_001',
            'name': '試験太郎',
            'use_date': '2025-01-10',
            'year': 2025,
            'month': 1,
            'days_used': 1.0
        },
        {
            'employee_num': 'TEST_EMP_001',
            'name': '試験太郎',
            'use_date': '2025-01-13',
            'year': 2025,
            'month': 1,
            'days_used': 0.5
        }
    ]


@pytest.fixture
def sample_leave_request_data():
    """Sample leave request data fixture."""
    return {
        'employee_num': 'TEST_EMP_001',
        'employee_name': '試験太郎',
        'start_date': '2025-02-10',
        'end_date': '2025-02-12',
        'days_requested': 3.0,
        'hours_requested': 0,
        'leave_type': 'full',
        'reason': 'テスト有給休暇申請',
        'year': 2025,
        'hourly_wage': 1500
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "pooling: mark test as a pooling test"
    )
    config.addinivalue_line(
        "markers",
        "skip_without_postgres: skip test if PostgreSQL is not configured"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests based on their location.
    """
    for item in items:
        # Mark tests by file location
        if "test_database_compatibility" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_postgresql_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_connection_pooling" in str(item.fspath):
            item.add_marker(pytest.mark.pooling)


# ============================================
# SHARED AUTH FIXTURES
# ============================================

@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


@pytest.fixture
def admin_auth_headers(test_client, reset_rate_limiter):
    """Get auth headers for admin user."""
    response = test_client.post("/api/auth/login", json={
        "username": TEST_ADMIN_USERNAME,
        "password": TEST_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    # Fallback for tests where auth may not be fully configured
    return {}


@pytest.fixture
def user_auth_headers(test_client, reset_rate_limiter):
    """Get auth headers for normal user."""
    response = test_client.post("/api/auth/login", json={
        "username": TEST_USER_USERNAME,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def csrf_token(test_client, reset_rate_limiter):
    """Get a CSRF token."""
    response = test_client.get("/api/csrf-token")
    if response.status_code == 200:
        data = response.json()
        return data.get("csrf_token", "")
    return ""
