"""YukyuUsageDetail ORM Model - Individual Leave Dates"""

from sqlalchemy import Column, String, Float, Integer, Index, ForeignKey
from orm.models.base import Base, BaseModel


class YukyuUsageDetail(BaseModel, Base):
    """
    Individual leave usage details.

    Stores individual dates when leave was taken, not just aggregates.

    Attributes:
        id: UUID primary key
        employee_num: Employee number (indexed, part of unique constraint)
        year: Fiscal year (indexed, part of unique constraint)
        usage_date: Date when leave was taken (YYYY-MM-DD)
        days_used: Days used on that date (1.0, 0.5, etc.)
        leave_type: Type of leave (full, half_am, half_pm, hourly)
        notes: Additional notes
        source: Source of data (excel, manual, api)
        created_at: When record was created
        updated_at: When record was last updated
    """

    __tablename__ = "yukyu_usage_details"

    employee_num = Column(String(12), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    usage_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    days_used = Column(Float, nullable=False)
    leave_type = Column(String(20), default="full")
    notes = Column(String(500))
    source = Column(String(50), default="manual")  # excel, manual, api

    __table_args__ = (
        Index('idx_usage_emp_year', 'employee_num', 'year'),
        Index('idx_usage_date', 'usage_date'),
        Index('idx_usage_emp_date', 'employee_num', 'usage_date'),
    )

    def __repr__(self):
        return f"<YukyuUsageDetail(id={self.id}, emp={self.employee_num}, date={self.usage_date})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        return {
            'id': self.id,
            'employee_num': self.employee_num,
            'year': self.year,
            'usage_date': self.usage_date,
            'days_used': self.days_used,
            'leave_type': self.leave_type,
            'notes': self.notes,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
