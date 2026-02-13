"""
SQLAlchemy ORM Models for YuKyuDATA
====================================

This module provides SQLAlchemy ORM models for database operations.
Separate from Pydantic schemas in models/ for cleaner architecture.

Models:
- Employee: Vacation data with UUID primary key
- LeaveRequest: Leave request workflow
- GenzaiEmployee: Dispatch employees
- UkeoiEmployee: Contract employees
- StaffEmployee: Office staff
- YukyuUsageDetail: Individual leave dates
- Notification: System notifications
- NotificationRead: Notification read status per user
- AuditLog: Complete audit trail
- User: System users

Architecture:
- UUID primary keys for scalability
- (employee_num, year) unique constraints
- Indexes on frequently queried fields
- Supports both SQLite and PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import os

# Base class for all ORM models
Base = declarative_base()

# Database URL from environment or default
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///yukyu.db'
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv('SQLALCHEMY_ECHO', 'false').lower() == 'true',
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import models to register them with Base
from orm.models.employee import Employee
from orm.models.leave_request import LeaveRequest
from orm.models.genzai_employee import GenzaiEmployee
from orm.models.ukeoi_employee import UkeoiEmployee
from orm.models.staff_employee import StaffEmployee
from orm.models.yukyu_usage_detail import YukyuUsageDetail
from orm.models.notification import Notification
from orm.models.notification_read import NotificationRead
from orm.models.audit_log import AuditLog
from orm.models.user import User
from orm.models.refresh_token import RefreshToken

__all__ = [
    'Base',
    'engine',
    'SessionLocal',
    'get_db_session',
    'Employee',
    'LeaveRequest',
    'GenzaiEmployee',
    'UkeoiEmployee',
    'StaffEmployee',
    'YukyuUsageDetail',
    'Notification',
    'NotificationRead',
    'AuditLog',
    'User',
    'RefreshToken',
]
