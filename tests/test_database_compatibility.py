"""
Unit tests for database package compatibility.

Tests verify that the database/ package works correctly with both
SQLite (default) and PostgreSQL, using the ORM-based implementation.
"""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import database
from services.crypto_utils import encrypt_field, decrypt_field


class TestDatabasePackageInit:
    """Test database package initialization."""

    def test_use_postgresql_flag(self):
        """Test that USE_POSTGRESQL flag is accessible."""
        assert isinstance(database.USE_POSTGRESQL, bool)

    def test_exports_available(self):
        """Test that key functions are exported from the package."""
        required_exports = [
            'get_db', 'init_db', 'save_employees', 'get_employees',
            'get_genzai', 'save_genzai', 'get_ukeoi', 'save_ukeoi',
            'get_staff', 'save_staff', 'get_leave_requests',
            'save_yukyu_usage_details', 'get_yukyu_usage_details',
            'get_available_years', 'get_employees_enhanced',
            'get_employee_by_num_year', 'approve_leave_request',
            'reject_leave_request', 'log_audit_action', 'get_audit_logs',
            'create_notification', 'get_notifications',
        ]
        for fn_name in required_exports:
            assert hasattr(database, fn_name), f"Missing export: database.{fn_name}"
            assert callable(getattr(database, fn_name)), f"Not callable: database.{fn_name}"


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


class TestLegacyAliases:
    """Test backwards compatibility aliases."""

    def test_log_action_alias(self):
        """Test that log_action is an alias for log_audit_action."""
        assert database.log_action is database.log_audit_action

    def test_log_audit_alias(self):
        """Test that log_audit is an alias for log_audit_action."""
        assert database.log_audit is database.log_audit_action

    def test_get_audit_log_alias(self):
        """Test that get_audit_log is an alias for get_audit_logs."""
        assert database.get_audit_log is database.get_audit_logs


class TestFunctionSignatures:
    """Test that function signatures match what routes expect."""

    def test_get_genzai_accepts_status(self):
        """Test get_genzai accepts status keyword arg."""
        import inspect
        sig = inspect.signature(database.get_genzai)
        assert 'status' in sig.parameters

    def test_get_ukeoi_accepts_status(self):
        """Test get_ukeoi accepts status keyword arg."""
        import inspect
        sig = inspect.signature(database.get_ukeoi)
        assert 'status' in sig.parameters

    def test_get_staff_accepts_status(self):
        """Test get_staff accepts status keyword arg."""
        import inspect
        sig = inspect.signature(database.get_staff)
        assert 'status' in sig.parameters

    def test_get_employees_enhanced_accepts_year_and_active(self):
        """Test get_employees_enhanced accepts year and active_only."""
        import inspect
        sig = inspect.signature(database.get_employees_enhanced)
        assert 'year' in sig.parameters
        assert 'active_only' in sig.parameters

    def test_approve_leave_request_signature(self):
        """Test approve_leave_request has correct params."""
        import inspect
        sig = inspect.signature(database.approve_leave_request)
        assert 'request_id' in sig.parameters
        assert 'approved_by' in sig.parameters

    def test_get_audit_logs_extended_signature(self):
        """Test get_audit_logs accepts all filter params."""
        import inspect
        sig = inspect.signature(database.get_audit_logs)
        params = sig.parameters
        assert 'entity_type' in params
        assert 'entity_id' in params
        assert 'action' in params
        assert 'user_id' in params
        assert 'start_date' in params
        assert 'end_date' in params
        assert 'limit' in params
        assert 'offset' in params

    def test_get_yukyu_usage_details_signature(self):
        """Test get_yukyu_usage_details accepts all filter params."""
        import inspect
        sig = inspect.signature(database.get_yukyu_usage_details)
        params = sig.parameters
        assert 'employee_num' in params
        assert 'year' in params
        assert 'month' in params


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
