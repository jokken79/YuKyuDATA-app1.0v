"""
Repository Pattern Implementation for YuKyuDATA

FASE 3: Repositories provide a data access layer abstraction.

This pattern:
1. Encapsulates CRUD operations per entity
2. Provides clean API for service layer
3. Allows easy testing with mock repositories
4. Centralizes database logic
5. Improves code maintainability

Usage:
    from repositories import get_employee_repository
    from orm import SessionLocal

    with SessionLocal() as session:
        repo = get_employee_repository(session)
        employees = repo.get_all(year=2025)
        employee = repo.get_by_id('emp_num_123', 2025)
"""

from repositories.employee_repository import EmployeeRepository
from repositories.leave_request_repository import LeaveRequestRepository
from repositories.genzai_repository import GenzaiRepository
from repositories.ukeoi_repository import UkeoiRepository
from repositories.staff_repository import StaffRepository
from repositories.yukyu_usage_detail_repository import YukyuUsageDetailRepository
from repositories.notification_repository import NotificationRepository
from repositories.user_repository import UserRepository
from repositories.audit_log_repository import AuditLogRepository


def get_employee_repository(session):
    """Factory for employee repository."""
    return EmployeeRepository(session)


def get_leave_request_repository(session):
    """Factory for leave request repository."""
    return LeaveRequestRepository(session)


def get_genzai_repository(session):
    """Factory for Genzai (dispatch) employee repository."""
    return GenzaiRepository(session)


def get_ukeoi_repository(session):
    """Factory for Ukeoi (contract) employee repository."""
    return UkeoiRepository(session)


def get_staff_repository(session):
    """Factory for staff repository."""
    return StaffRepository(session)


def get_yukyu_usage_detail_repository(session):
    """Factory for yukyu usage detail repository."""
    return YukyuUsageDetailRepository(session)


def get_notification_repository(session):
    """Factory for notification repository."""
    return NotificationRepository(session)


def get_user_repository(session):
    """Factory for user repository."""
    return UserRepository(session)


def get_audit_log_repository(session):
    """Factory for audit log repository."""
    return AuditLogRepository(session)


__all__ = [
    'EmployeeRepository',
    'LeaveRequestRepository',
    'GenzaiRepository',
    'UkeoiRepository',
    'StaffRepository',
    'YukyuUsageDetailRepository',
    'NotificationRepository',
    'UserRepository',
    'AuditLogRepository',
    'get_employee_repository',
    'get_leave_request_repository',
    'get_genzai_repository',
    'get_ukeoi_repository',
    'get_staff_repository',
    'get_yukyu_usage_detail_repository',
    'get_notification_repository',
    'get_user_repository',
    'get_audit_log_repository',
]
