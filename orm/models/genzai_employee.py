"""GenzaiEmployee ORM Model - Dispatch Employees"""

from sqlalchemy import Column, String, Float, Integer, Index
from orm.models.base import Base, BaseModel


class GenzaiEmployee(BaseModel, Base):
    """
    Dispatch employee (派遣社員) data.

    Attributes:
        id: UUID primary key
        status: Employment status (在職中, 退職)
        employee_num: Employee number (unique, indexed)
        dispatch_id: Dispatch ID from registry
        dispatch_name: Dispatch company name
        department: Department
        line: Production line
        job_content: Job description
        name: Employee name
        kana: Name in Katakana
        gender: Gender
        nationality: Nationality
        birth_date: Birth date
        age: Current age
        hourly_wage: Hourly wage
        wage_revision: Last wage revision date
        hire_date: Hire date
        leave_date: Leave/termination date
        created_at: Record created timestamp
        updated_at: Record updated timestamp
    """

    __tablename__ = "genzai"

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
        Index('idx_genzai_status', 'status'),
        Index('idx_genzai_emp_num', 'employee_num'),
        Index('idx_genzai_dispatch', 'dispatch_id'),
    )

    def __repr__(self):
        return f"<GenzaiEmployee(id={self.id}, emp_num={self.employee_num}, name={self.name})>"

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
