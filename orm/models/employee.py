"""Employee ORM Model - Vacation Data"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Index, UniqueConstraint
from orm.models.base import Base, BaseModel


class Employee(BaseModel, Base):
    """
    Employee vacation data with UUID primary key.

    FASE 3 Migration: Changed from composite key {employee_num}_{year} to UUID.
    Maintains unique constraint on (employee_num, year) for compatibility.

    Attributes:
        id: UUID primary key
        employee_num: Employee number (indexed, part of unique constraint)
        year: Fiscal year (indexed, part of unique constraint)
        name: Employee name
        haken: Workplace/dispatch location
        granted: Days granted for the year
        used: Days used
        balance: Days remaining
        expired: Days that expired
        usage_rate: Usage percentage
        last_updated: Legacy field (kept for compatibility)
        created_at: Timestamp when record created
        updated_at: Timestamp when record updated
    """

    __tablename__ = "employees"

    employee_num = Column(String(12), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    name = Column(String(100))
    haken = Column(String(100))
    granted = Column(Float, default=0.0)
    used = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    expired = Column(Float, default=0.0)
    usage_rate = Column(Float, default=0.0)
    last_updated = Column(String(50))  # Legacy field

    # Unique constraint on (employee_num, year)
    __table_args__ = (
        UniqueConstraint('employee_num', 'year', name='uq_emp_year'),
        Index('idx_emp_year', 'employee_num', 'year'),
        Index('idx_emp_created', 'employee_num', 'created_at'),
        Index('idx_year_updated', 'year', 'updated_at'),
    )

    def __repr__(self):
        return f"<Employee(id={self.id}, emp_num={self.employee_num}, year={self.year}, name={self.name})>"

    def to_dict(self):
        """Convert to dict with all vacation fields."""
        return {
            'id': self.id,
            'employee_num': self.employee_num,
            'year': self.year,
            'name': self.name,
            'haken': self.haken,
            'granted': self.granted,
            'used': self.used,
            'balance': self.balance,
            'expired': self.expired,
            'usage_rate': self.usage_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
