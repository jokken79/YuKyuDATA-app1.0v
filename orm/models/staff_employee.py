"""StaffEmployee ORM Model - Office Staff"""

from sqlalchemy import Column, String, Float, Integer, Index
from sqlalchemy.orm import declarative_base
from orm.models.base import BaseModel

Base = declarative_base()


class StaffEmployee(BaseModel, Base):
    """
    Office staff employee data.

    Similar structure to GenzaiEmployee but for office staff.
    """

    __tablename__ = "staff"

    status = Column(String(20))  # 在職中, 退職
    employee_num = Column(String(12), unique=True, index=True)
    dispatch_id = Column(String(50))
    dispatch_name = Column(String(100))
    department = Column(String(100))
    line = Column(String(100))
    job_content = Column(String(200))
    name = Column(String(100))
    kana = Column(String(100))
    gender = Column(String(10))
    nationality = Column(String(50))
    birth_date = Column(String(10))  # YYYY-MM-DD
    age = Column(Integer)
    hourly_wage = Column(Float)
    wage_revision = Column(String(10))  # YYYY-MM-DD
    hire_date = Column(String(10))  # YYYY-MM-DD
    leave_date = Column(String(10))  # YYYY-MM-DD

    __table_args__ = (
        Index('idx_staff_status', 'status'),
        Index('idx_staff_emp_num', 'employee_num'),
        Index('idx_staff_dispatch', 'dispatch_id'),
    )

    def __repr__(self):
        return f"<StaffEmployee(id={self.id}, emp_num={self.employee_num}, name={self.name})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        return {
            'id': self.id,
            'status': self.status,
            'employee_num': self.employee_num,
            'dispatch_id': self.dispatch_id,
            'dispatch_name': self.dispatch_name,
            'department': self.department,
            'line': self.line,
            'job_content': self.job_content,
            'name': self.name,
            'kana': self.kana,
            'gender': self.gender,
            'nationality': self.nationality,
            'birth_date': self.birth_date,
            'age': self.age,
            'hourly_wage': self.hourly_wage,
            'wage_revision': self.wage_revision,
            'hire_date': self.hire_date,
            'leave_date': self.leave_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
