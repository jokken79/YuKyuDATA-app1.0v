"""
Custom Exception Classes
Standardized exceptions for better error handling and meaningful HTTP responses
"""

from typing import Optional


class YuKyuException(Exception):
    """Base exception for all YuKyuDATA exceptions"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class EmployeeNotFoundException(YuKyuException):
    """Raised when an employee cannot be found"""
    
    def __init__(self, employee_id: str, details: Optional[dict] = None):
        message = f"Employee not found: {employee_id}"
        super().__init__(message, details)
        self.employee_id = employee_id


class InvalidDataException(YuKyuException):
    """Raised when provided data is invalid or malformed"""
    
    def __init__(self, field: str, reason: str, details: Optional[dict] = None):
        message = f"Invalid data for field '{field}': {reason}"
        super().__init__(message, details)
        self.field = field
        self.reason = reason


class AuthenticationException(YuKyuException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[dict] = None):
        super().__init__(message, details)


class AuthorizationException(YuKyuException):
    """Raised when user lacks required permissions"""
    
    def __init__(self, required_role: Optional[str] = None, details: Optional[dict] = None):
        message = "Insufficient permissions"
        if required_role:
            message += f". Required role: {required_role}"
        super().__init__(message, details)
        self.required_role = required_role


class DatabaseException(YuKyuException):
    """Raised when database operations fail"""
    
    def __init__(self, operation: str, reason: str, details: Optional[dict] = None):
        message = f"Database operation '{operation}' failed: {reason}"
        super().__init__(message, details)
        self.operation = operation
        self.reason = reason


class ValidationException(YuKyuException):
    """Raised when data validation fails"""
    
    def __init__(self, errors: dict, details: Optional[dict] = None):
        message = "Validation failed"
        super().__init__(message, details)
        self.errors = errors


class ResourceNotFoundException(YuKyuException):
    """Raised when a requested resource cannot be found"""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[dict] = None):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class ExcelParseException(YuKyuException):
    """Raised when Excel file parsing fails"""
    
    def __init__(self, filename: str, reason: str, details: Optional[dict] = None):
        message = f"Failed to parse Excel file '{filename}': {reason}"
        super().__init__(message, details)
        self.filename = filename
        self.reason = reason


class SyncException(YuKyuException):
    """Raised when data synchronization fails"""
    
    def __init__(self, source: str, reason: str, details: Optional[dict] = None):
        message = f"Synchronization from '{source}' failed: {reason}"
        super().__init__(message, details)
        self.source = source
        self.reason = reason


class RateLimitException(YuKyuException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, retry_after: int, details: Optional[dict] = None):
        message = f"Rate limit exceeded. Retry after {retry_after} seconds."
        super().__init__(message, details)
        self.retry_after = retry_after
