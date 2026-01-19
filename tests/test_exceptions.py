"""
Tests for Custom Exceptions
Tests exception handling and HTTP status code mapping
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from exceptions.custom_exceptions import (
    YuKyuException,
    EmployeeNotFoundException,
    InvalidDataException,
    AuthenticationException,
    AuthorizationException,
    DatabaseException,
    ValidationException,
    ResourceNotFoundException,
    ExcelParseException,
    SyncException,
    RateLimitException
)


class TestYuKyuException:
    """Test base exception class"""
    
    def test_create_basic_exception(self):
        """Test creating basic exception"""
        exc = YuKyuException("Test error message")
        
        assert str(exc) == "Test error message"
        assert exc.message == "Test error message"
        assert exc.details == {}
    
    def test_create_exception_with_details(self):
        """Test exception with details"""
        details = {"field": "username", "value": "test"}
        exc = YuKyuException("Error occurred", details=details)
        
        assert exc.message == "Error occurred"
        assert exc.details == details


class TestEmployeeNotFoundException:
    """Test employee not found exception"""
    
    def test_employee_not_found(self):
        """Test employee not found exception"""
        exc = EmployeeNotFoundException("EMP123")
        
        assert "EMP123" in str(exc)
        assert exc.employee_id == "EMP123"
    
    def test_employee_not_found_with_details(self):
        """Test with additional details"""
        details = {"attempted_search": "by_number"}
        exc = EmployeeNotFoundException("EMP456", details=details)
        
        assert exc.details == details


class TestInvalidDataException:
    """Test invalid data exception"""
    
    def test_invalid_data(self):
        """Test invalid data exception"""
        exc = InvalidDataException("email", "Invalid format")
        
        assert "email" in str(exc)
        assert "Invalid format" in str(exc)
        assert exc.field == "email"
        assert exc.reason == "Invalid format"


class TestAuthenticationException:
    """Test authentication exception"""
    
    def test_authentication_error(self):
        """Test authentication exception"""
        exc = AuthenticationException("Invalid credentials")
        
        assert str(exc) == "Invalid credentials"
    
    def test_default_message(self):
        """Test default authentication message"""
        exc = AuthenticationException()
        
        assert "Authentication failed" in str(exc)


class TestAuthorizationException:
    """Test authorization exception"""
    
    def test_authorization_error(self):
        """Test authorization exception"""
        exc = AuthorizationException(required_role="admin")
        
        assert "admin" in str(exc)
        assert exc.required_role == "admin"
    
    def test_authorization_no_role(self):
        """Test authorization without specific role"""
        exc = AuthorizationException()
        
        assert "permissions" in str(exc).lower()


class TestDatabaseException:
    """Test database exception"""
    
    def test_database_error(self):
        """Test database exception"""
        exc = DatabaseException("insert", "Connection timeout")
        
        assert "insert" in str(exc)
        assert "Connection timeout" in str(exc)
        assert exc.operation == "insert"
        assert exc.reason == "Connection timeout"


class TestValidationException:
    """Test validation exception"""
    
    def test_validation_error(self):
        """Test validation exception"""
        errors = {
            "username": "Required field",
            "email": "Invalid format"
        }
        exc = ValidationException(errors)
        
        assert exc.errors == errors
        assert "Validation failed" in str(exc)


class TestResourceNotFoundException:
    """Test resource not found exception"""
    
    def test_resource_not_found(self):
        """Test resource not found exception"""
        exc = ResourceNotFoundException("Report", "report_123")
        
        assert "Report" in str(exc)
        assert "report_123" in str(exc)
        assert exc.resource_type == "Report"
        assert exc.resource_id == "report_123"


class TestExcelParseException:
    """Test Excel parse exception"""
    
    def test_excel_parse_error(self):
        """Test Excel parse exception"""
        exc = ExcelParseException("employees.xlsx", "Invalid header row")
        
        assert "employees.xlsx" in str(exc)
        assert "Invalid header row" in str(exc)
        assert exc.filename == "employees.xlsx"
        assert exc.reason == "Invalid header row"


class TestSyncException:
    """Test sync exception"""
    
    def test_sync_error(self):
        """Test sync exception"""
        exc = SyncException("Excel", "File not found")
        
        assert "Excel" in str(exc)
        assert "File not found" in str(exc)
        assert exc.source == "Excel"
        assert exc.reason == "File not found"


class TestRateLimitException:
    """Test rate limit exception"""
    
    def test_rate_limit_error(self):
        """Test rate limit exception"""
        exc = RateLimitException(retry_after=60)
        
        assert "60" in str(exc)
        assert exc.retry_after == 60
        assert "Rate limit" in str(exc)


class TestExceptionHierarchy:
    """Test exception class hierarchy"""
    
    def test_all_inherit_from_base(self):
        """Test all custom exceptions inherit from YuKyuException"""
        exceptions = [
            EmployeeNotFoundException("EMP1"),
            InvalidDataException("field", "reason"),
            AuthenticationException(),
            AuthorizationException(),
            DatabaseException("op", "reason"),
            ValidationException({}),
            ResourceNotFoundException("Type", "id"),
            ExcelParseException("file", "reason"),
            SyncException("source", "reason"),
            RateLimitException(60)
        ]
        
        for exc in exceptions:
            assert isinstance(exc, YuKyuException)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
