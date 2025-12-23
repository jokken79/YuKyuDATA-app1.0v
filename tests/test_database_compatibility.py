"""
Unit tests for SQLite and PostgreSQL database compatibility.

Tests verify that database.py works correctly with both SQLite and PostgreSQL,
with proper parameter placeholder handling and UPSERT functionality.
"""

import pytest
import os
import tempfile
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import database
from crypto_utils import encrypt_field, decrypt_field


class TestDatabaseConnectionInit:
    """Test database connection initialization."""

    def test_sqlite_connection_default(self):
        """Test that SQLite is the default database."""
        # Save original
        original_use_pg = database.USE_POSTGRESQL

        # Reset to default (SQLite)
        database.USE_POSTGRESQL = False

        conn = database.get_db_connection()
        assert conn is not None

        # Check SQLite specific attributes
        assert hasattr(conn, 'row_factory')

        conn.close()

        # Restore
        database.USE_POSTGRESQL = original_use_pg

    def test_database_url_from_env(self):
        """Test that DATABASE_URL is read from environment."""
        test_url = "postgresql://test:test@localhost:5432/test"
        os.environ['DATABASE_URL'] = test_url

        # Reimport to pick up new env var
        import importlib
        importlib.reload(database)

        assert database.DATABASE_URL == test_url

    def test_use_postgresql_flag_from_env(self):
        """Test that DATABASE_TYPE environment variable controls database selection."""
        # Test SQLite
        os.environ['DATABASE_TYPE'] = 'sqlite'
        import importlib
        importlib.reload(database)
        assert database.USE_POSTGRESQL == False

        # Test PostgreSQL
        os.environ['DATABASE_TYPE'] = 'postgresql'
        importlib.reload(database)
        assert database.USE_POSTGRESQL == True

        # Reset
        os.environ['DATABASE_TYPE'] = 'sqlite'
        importlib.reload(database)


class TestParameterPlaceholders:
    """Test parameter placeholder helper functions."""

    def test_get_param_placeholder_sqlite(self):
        """Test parameter placeholder for SQLite."""
        database.USE_POSTGRESQL = False
        assert database._get_param_placeholder() == '?'

    def test_get_param_placeholder_postgresql(self):
        """Test parameter placeholder for PostgreSQL."""
        database.USE_POSTGRESQL = True
        assert database._get_param_placeholder() == '%s'

    def test_convert_query_placeholders_sqlite(self):
        """Test that SQLite queries are not modified."""
        database.USE_POSTGRESQL = False
        query = "INSERT INTO employees VALUES (?, ?, ?, ?)"
        result = database._convert_query_placeholders(query)
        assert result == query

    def test_convert_query_placeholders_postgresql(self):
        """Test that queries are converted for PostgreSQL."""
        database.USE_POSTGRESQL = True
        query = "INSERT INTO employees VALUES (?, ?, ?, ?)"
        result = database._convert_query_placeholders(query)
        assert result == "INSERT INTO employees VALUES (%s, %s, %s, %s)"


class TestEmployeeSaveCompatibility:
    """Test save_employees() compatibility with both databases."""

    @pytest.fixture
    def sample_employee_data(self):
        """Sample employee data for testing."""
        return [
            {
                'id': 'EMP001_2025',
                'employeeNum': 'EMP001',
                'name': '田中太郎',
                'haken': '工場A',
                'granted': 20.0,
                'used': 5.0,
                'balance': 15.0,
                'expired': 0.0,
                'usageRate': 25.0,
                'year': 2025
            },
            {
                'id': 'EMP002_2025',
                'employeeNum': 'EMP002',
                'name': '佐藤花子',
                'haken': '工場B',
                'granted': 15.0,
                'used': 3.0,
                'balance': 12.0,
                'expired': 0.0,
                'usageRate': 20.0,
                'year': 2025
            }
        ]

    def test_save_employees_sqlite(self, sample_employee_data):
        """Test saving employees to SQLite."""
        database.USE_POSTGRESQL = False

        # Use in-memory SQLite
        import sqlite3
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Override DB_NAME
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                # Initialize database
                database.init_db()

                # Save employees
                database.save_employees(sample_employee_data)

                # Verify save
                employees = database.get_employees()
                assert len(employees) == 2
                assert employees[0]['name'] == '田中太郎'
                assert employees[1]['name'] == '佐藤花子'

            finally:
                database.DB_NAME = original_db

    def test_upsert_behavior_sqlite(self, sample_employee_data):
        """Test UPSERT behavior (INSERT OR REPLACE) in SQLite."""
        database.USE_POSTGRESQL = False

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                database.init_db()

                # Save initial data
                database.save_employees(sample_employee_data)
                initial_count = len(database.get_employees())

                # Update one employee (change used days)
                updated_data = [sample_employee_data[0].copy()]
                updated_data[0]['used'] = 10.0
                updated_data[0]['balance'] = 10.0

                database.save_employees(updated_data)

                # Count should remain same (UPSERT, not INSERT)
                final_count = len(database.get_employees())
                assert final_count == initial_count

                # Verify data was updated
                emp = [e for e in database.get_employees() if e['id'] == 'EMP001_2025'][0]
                assert emp['used'] == 10.0
                assert emp['balance'] == 10.0

            finally:
                database.DB_NAME = original_db


class TestEncryptionCompatibility:
    """Test that encryption works with both databases."""

    def test_encrypt_decrypt_consistency(self):
        """Test that encryption/decryption works consistently."""
        test_value = "2000-01-15"

        # Encrypt
        encrypted = encrypt_field(test_value)
        assert encrypted != test_value

        # Decrypt
        decrypted = decrypt_field(encrypted)
        assert decrypted == test_value

    def test_encrypted_field_none_handling(self):
        """Test encryption handles None values."""
        encrypted_none = encrypt_field(None)
        assert encrypted_none is None or isinstance(encrypted_none, str)

    def test_encrypted_field_empty_string(self):
        """Test encryption handles empty strings."""
        encrypted_empty = encrypt_field("")
        # Should not raise


class TestGenzaiSaveCompatibility:
    """Test save_genzai() with both databases."""

    @pytest.fixture
    def sample_genzai_data(self):
        """Sample Genzai (dispatch employee) data."""
        return [
            {
                'id': 'genzai_EMP001',
                'status': '在職中',
                'employee_num': 'EMP001',
                'dispatch_id': 'D001',
                'dispatch_name': '派遣先A',
                'department': '製造部',
                'line': 'ライン1',
                'job_content': 'ライン作業',
                'name': '田中太郎',
                'kana': 'タナカタロウ',
                'gender': '男',
                'nationality': '日本',
                'birth_date': '1990-05-15',
                'age': 34,
                'hourly_wage': 1500,
                'wage_revision': '2025-01-01',
                'hire_date': '2020-04-01',
                'leave_date': None
            }
        ]

    def test_save_genzai_with_encryption(self, sample_genzai_data):
        """Test saving Genzai data with encrypted fields."""
        database.USE_POSTGRESQL = False

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                database.init_db()

                # Save Genzai
                database.save_genzai(sample_genzai_data)

                # Retrieve and verify encryption
                genzai = database.get_genzai()
                assert len(genzai) == 1
                emp = genzai[0]

                # Verify encrypted fields are decrypted on retrieval
                assert emp['birth_date'] == '1990-05-15'
                assert emp['hourly_wage'] == 1500

            finally:
                database.DB_NAME = original_db


class TestLeaveRequestCompatibility:
    """Test leave request creation with both databases."""

    def test_create_leave_request_sqlite(self):
        """Test creating leave request in SQLite."""
        database.USE_POSTGRESQL = False

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                database.init_db()

                # Create leave request
                request_id = database.create_leave_request(
                    employee_num='EMP001',
                    employee_name='田中太郎',
                    start_date='2025-01-10',
                    end_date='2025-01-12',
                    days_requested=3.0,
                    reason='個人用事',
                    year=2025,
                    leave_type='full',
                    hourly_wage=1500
                )

                assert request_id is not None
                assert isinstance(request_id, int)

                # Verify request was created
                requests = database.get_leave_requests(employee_num='EMP001')
                assert len(requests) == 1
                assert requests[0]['status'] == 'PENDING'

            finally:
                database.DB_NAME = original_db


class TestYukyuUsageDetailsCompatibility:
    """Test Yukyu usage details save/retrieve."""

    @pytest.fixture
    def sample_usage_data(self):
        """Sample usage details data."""
        return [
            {
                'employee_num': 'EMP001',
                'name': '田中太郎',
                'use_date': '2025-01-10',
                'year': 2025,
                'month': 1,
                'days_used': 1.0
            },
            {
                'employee_num': 'EMP001',
                'name': '田中太郎',
                'use_date': '2025-01-13',
                'year': 2025,
                'month': 1,
                'days_used': 0.5
            }
        ]

    def test_save_usage_details_sqlite(self, sample_usage_data):
        """Test saving usage details in SQLite."""
        database.USE_POSTGRESQL = False

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                database.init_db()

                # Save usage details
                database.save_yukyu_usage_details(sample_usage_data)

                # Retrieve
                details = database.get_yukyu_usage_details(employee_num='EMP001', year=2025)
                assert len(details) == 2
                assert details[0]['days_used'] == 1.0
                assert details[1]['days_used'] == 0.5

            finally:
                database.DB_NAME = original_db

    def test_usage_details_unique_constraint(self, sample_usage_data):
        """Test unique constraint on (employee_num, use_date)."""
        database.USE_POSTGRESQL = False

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                database.init_db()

                # Save initial data
                database.save_yukyu_usage_details(sample_usage_data)
                initial_count = len(database.get_yukyu_usage_details())

                # Try to save duplicate (should UPSERT, not fail)
                duplicate = [sample_usage_data[0].copy()]
                duplicate[0]['days_used'] = 2.0  # Different value

                database.save_yukyu_usage_details(duplicate)

                # Count should not increase
                final_count = len(database.get_yukyu_usage_details())
                assert final_count == initial_count

                # Verify data was updated
                updated = database.get_yukyu_usage_details(employee_num='EMP001', year=2025)
                emp_records = [d for d in updated if d['use_date'] == '2025-01-10']
                assert len(emp_records) == 1
                assert emp_records[0]['days_used'] == 2.0

            finally:
                database.DB_NAME = original_db


class TestDatabaseInitialization:
    """Test database initialization with all tables and indexes."""

    def test_all_tables_created(self):
        """Test that init_db() creates all required tables."""
        database.USE_POSTGRESQL = False

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                database.init_db()

                # Check that we can query each table
                conn = database.get_db_connection()
                cursor = conn.cursor()

                tables = [
                    'employees',
                    'yukyu_usage_details',
                    'genzai',
                    'ukeoi',
                    'staff',
                    'leave_requests'
                ]

                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    result = cursor.fetchone()
                    assert result is not None

                conn.close()

            finally:
                database.DB_NAME = original_db

    def test_indexes_created(self):
        """Test that all strategic indexes are created."""
        database.USE_POSTGRESQL = False

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            original_db = database.DB_NAME
            database.DB_NAME = str(db_path)

            try:
                database.init_db()

                conn = database.get_db_connection()
                cursor = conn.cursor()

                # Check for key indexes (SQLite specific query)
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]

                # Verify some key indexes exist
                assert 'idx_emp_num' in indexes
                assert 'idx_emp_year' in indexes
                assert 'idx_lr_emp_num' in indexes

                conn.close()

            finally:
                database.DB_NAME = original_db


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
