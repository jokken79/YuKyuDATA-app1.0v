"""
Dependency Injection Container for YuKyuDATA

FASE 3: FastAPI dependency injection setup with repository pattern.

This module provides:
- Database session dependency
- Repository factories as dependencies
- Service dependencies
- Middleware and auth dependencies

Usage in routes:
    from fastapi import Depends
    from di import get_employee_repo, get_leave_request_repo
    from orm import SessionLocal

    @app.get("/api/employees/{year}")
    async def get_employees(
        year: int,
        employee_repo: EmployeeRepository = Depends(get_employee_repo),
        leave_repo: LeaveRequestRepository = Depends(get_leave_request_repo)
    ):
        employees = employee_repo.get_by_year(year)
        return {"data": [e.to_dict() for e in employees]}
"""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from orm import SessionLocal
from repositories import (
    EmployeeRepository,
    LeaveRequestRepository,
    GenzaiRepository,
    UkeoiRepository,
    StaffRepository,
    YukyuUsageDetailRepository,
    NotificationRepository,
    UserRepository,
    AuditLogRepository,
)
from repositories import (
    get_employee_repository,
    get_leave_request_repository,
    get_genzai_repository,
    get_ukeoi_repository,
    get_staff_repository,
    get_yukyu_usage_detail_repository,
    get_notification_repository,
    get_user_repository,
    get_audit_log_repository,
)


# ============================================================================
# Database Session Dependency
# ============================================================================

def get_db_session() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI.

    Provides a SQLAlchemy session that is automatically closed after
    the request completes, preventing connection leaks.

    Usage:
        @app.get("/api/endpoint")
        async def endpoint(db: Session = Depends(get_db_session)):
            # use db...
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.commit()  # Auto-commit changes
        db.close()


def get_db_session_no_commit() -> Generator[Session, None, None]:
    """
    Database session dependency WITHOUT auto-commit.

    Use this when you need manual transaction control.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Repository Dependencies (Factory Pattern)
# ============================================================================

def get_employee_repo(
    db: Session = Depends(get_db_session)
) -> EmployeeRepository:
    """Get employee repository dependency."""
    return get_employee_repository(db)


def get_leave_request_repo(
    db: Session = Depends(get_db_session)
) -> LeaveRequestRepository:
    """Get leave request repository dependency."""
    return get_leave_request_repository(db)


def get_genzai_repo(
    db: Session = Depends(get_db_session)
) -> GenzaiRepository:
    """Get Genzai (dispatch) employee repository dependency."""
    return get_genzai_repository(db)


def get_ukeoi_repo(
    db: Session = Depends(get_db_session)
) -> UkeoiRepository:
    """Get Ukeoi (contract) employee repository dependency."""
    return get_ukeoi_repository(db)


def get_staff_repo(
    db: Session = Depends(get_db_session)
) -> StaffRepository:
    """Get staff repository dependency."""
    return get_staff_repository(db)


def get_yukyu_usage_detail_repo(
    db: Session = Depends(get_db_session)
) -> YukyuUsageDetailRepository:
    """Get Yukyu usage detail repository dependency."""
    return get_yukyu_usage_detail_repository(db)


def get_notification_repo(
    db: Session = Depends(get_db_session)
) -> NotificationRepository:
    """Get notification repository dependency."""
    return get_notification_repository(db)


def get_user_repo(
    db: Session = Depends(get_db_session)
) -> UserRepository:
    """Get user repository dependency."""
    return get_user_repository(db)


def get_audit_log_repo(
    db: Session = Depends(get_db_session)
) -> AuditLogRepository:
    """Get audit log repository dependency."""
    return get_audit_log_repository(db)


# ============================================================================
# Multi-Repository Dependencies
# ============================================================================

class RepositoryContainer:
    """
    Container for multiple repositories.

    Usage:
        @app.get("/api/dashboard")
        async def get_dashboard(
            repos: RepositoryContainer = Depends(get_repositories)
        ):
            employees = repos.employees.get_by_year(2025)
            requests = repos.leave_requests.get_pending(2025)
    """

    def __init__(
        self,
        employees: EmployeeRepository,
        leave_requests: LeaveRequestRepository,
        genzai: GenzaiRepository,
        ukeoi: UkeoiRepository,
        staff: StaffRepository,
        yukyu_details: YukyuUsageDetailRepository,
        notifications: NotificationRepository,
        users: UserRepository,
        audit_logs: AuditLogRepository,
    ):
        self.employees = employees
        self.leave_requests = leave_requests
        self.genzai = genzai
        self.ukeoi = ukeoi
        self.staff = staff
        self.yukyu_details = yukyu_details
        self.notifications = notifications
        self.users = users
        self.audit_logs = audit_logs


def get_repositories(
    employees: EmployeeRepository = Depends(get_employee_repo),
    leave_requests: LeaveRequestRepository = Depends(get_leave_request_repo),
    genzai: GenzaiRepository = Depends(get_genzai_repo),
    ukeoi: UkeoiRepository = Depends(get_ukeoi_repo),
    staff: StaffRepository = Depends(get_staff_repo),
    yukyu_details: YukyuUsageDetailRepository = Depends(get_yukyu_usage_detail_repo),
    notifications: NotificationRepository = Depends(get_notification_repo),
    users: UserRepository = Depends(get_user_repo),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repo),
) -> RepositoryContainer:
    """Get all repositories as a single container."""
    return RepositoryContainer(
        employees=employees,
        leave_requests=leave_requests,
        genzai=genzai,
        ukeoi=ukeoi,
        staff=staff,
        yukyu_details=yukyu_details,
        notifications=notifications,
        users=users,
        audit_logs=audit_logs,
    )


__all__ = [
    'get_db_session',
    'get_db_session_no_commit',
    'get_employee_repo',
    'get_leave_request_repo',
    'get_genzai_repo',
    'get_ukeoi_repo',
    'get_staff_repo',
    'get_yukyu_usage_detail_repo',
    'get_notification_repo',
    'get_user_repo',
    'get_audit_log_repo',
    'get_repositories',
    'RepositoryContainer',
]
