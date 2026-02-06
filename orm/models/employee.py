"""Employee ORM Model - Vacation Data"""

from sqlalchemy import Column, String, Float, Integer, DateTime, Index, UniqueConstraint
from orm.models.base import Base, BaseModel


class Employee(BaseModel, Base):
    """
    Employee vacation data with UUID primary key.

    Unique constraint on (employee_num, year, grant_date) to preserve
    all grant periods per employee per year.

    Attributes:
        id: UUID primary key
        employee_num: Employee number (indexed)
        year: Fiscal year (indexed)
        name: Employee name
        haken: Workplace/dispatch location
        granted: Days granted for the period
        used: Days used
        balance: End-of-period balance (期末残高)
        expired: Days expired (時効数)
        after_expiry: Balance after expiry (時効後残)
        usage_rate: Usage percentage
        grant_date: Date when leave was granted (有給発生) YYYY-MM-DD
        status: Employment status (在職中/退職)
        kana: Katakana name (カナ)
        hire_date: Hire date (入社日) YYYY-MM-DD
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
    after_expiry = Column(Float, default=0.0)
    usage_rate = Column(Float, default=0.0)
    grant_date = Column(String(10))  # YYYY-MM-DD
    status = Column(String(20))  # 在職中, 退職
    kana = Column(String(100))  # katakana name
    hire_date = Column(String(10))  # YYYY-MM-DD
    last_updated = Column(String(50))  # Legacy field

    # Unique constraint on (employee_num, year, grant_date) to preserve all grant periods
    __table_args__ = (
        UniqueConstraint('employee_num', 'year', 'grant_date', name='uq_emp_year_grant'),
        Index('idx_emp_year', 'employee_num', 'year'),
        Index('idx_emp_created', 'employee_num', 'created_at'),
        Index('idx_year_updated', 'year', 'updated_at'),
        Index('idx_emp_status', 'status'),
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
            'after_expiry': self.after_expiry,
            'usage_rate': self.usage_rate,
            'grant_date': self.grant_date,
            'status': self.status,
            'kana': self.kana,
            'hire_date': self.hire_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
