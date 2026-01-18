"""LeaveRequest ORM Model - Leave Request Workflow"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Index, Enum
from sqlalchemy.orm import declarative_base
from orm.models.base import BaseModel
from datetime import datetime
import enum

Base = declarative_base()


class LeaveStatus(str, enum.Enum):
    """Leave request status enum"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LeaveType(str, enum.Enum):
    """Leave type enum"""
    FULL = "full"
    HALF_AM = "half_am"
    HALF_PM = "half_pm"
    HOURLY = "hourly"


class LeaveRequest(BaseModel, Base):
    """
    Leave request with complete workflow.

    Workflow: PENDING → APPROVED/REJECTED → (optional) REVERTED

    Attributes:
        id: UUID primary key
        employee_num: Employee number (indexed)
        employee_name: Employee name (cached for reports)
        start_date: Leave start date (YYYY-MM-DD)
        end_date: Leave end date (YYYY-MM-DD)
        days_requested: Number of days requested
        hours_requested: Hours if hourly leave
        leave_type: Type of leave (full, half_am, half_pm, hourly)
        reason: Reason for leave request
        status: Current status (PENDING, APPROVED, REJECTED)
        year: Fiscal year
        hourly_wage: Hourly wage for hourly leave
        approver: User who approved/rejected
        approved_at: Timestamp of approval/rejection
        created_at: Timestamp when request created
        updated_at: Timestamp when request updated
    """

    __tablename__ = "leave_requests"

    employee_num = Column(String(12), nullable=False, index=True)
    employee_name = Column(String(100))
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)    # YYYY-MM-DD
    days_requested = Column(Float, nullable=False)
    hours_requested = Column(Integer, default=0)
    leave_type = Column(String(20), default="full")  # full, half_am, half_pm, hourly
    reason = Column(String(500))
    status = Column(String(20), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    year = Column(Integer, nullable=False, index=True)
    hourly_wage = Column(Float)
    approver = Column(String(100))
    approved_at = Column(DateTime)

    __table_args__ = (
        Index('idx_emp_status', 'employee_num', 'status'),
        Index('idx_year_status', 'year', 'status'),
        Index('idx_start_end', 'start_date', 'end_date'),
        Index('idx_approved_at', 'approved_at'),
    )

    def __repr__(self):
        return f"<LeaveRequest(id={self.id}, emp={self.employee_num}, status={self.status})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        return {
            'id': self.id,
            'employee_num': self.employee_num,
            'employee_name': self.employee_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'days_requested': self.days_requested,
            'hours_requested': self.hours_requested,
            'leave_type': self.leave_type,
            'reason': self.reason,
            'status': self.status,
            'year': self.year,
            'hourly_wage': self.hourly_wage,
            'approver': self.approver,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
