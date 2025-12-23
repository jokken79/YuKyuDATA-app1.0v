"""
Shared pytest fixtures and configuration for YuKyuDATA tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


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
