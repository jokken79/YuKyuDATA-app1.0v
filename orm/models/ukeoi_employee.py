"""UkeoiEmployee ORM Model - Contract Employees"""

from sqlalchemy import Column, String, Float, Integer, Index
from orm.models.base import Base, BaseModel


class UkeoiEmployee(BaseModel, Base):
    """
    Contract employee (請負社員) data.

    Similar structure to GenzaiEmployee but for contract workers.
    """

    __tablename__ = "ukeoi"

    status = Column(String(20))  # 在職中, 退職
    employee_num = Column(String(12), unique=True, index=True)
    contract_business = Column(String(200))  # 請負業務
    name = Column(String(100))
    kana = Column(String(100))
    gender = Column(String(10))
    nationality = Column(String(50))
    birth_date = Column(String(10))  # YYYY-MM-DD
    age = Column(Integer)
    hourly_wage = Column(Float)
    wage_revision = Column(String(10))  # YYYY-MM-DD

    __table_args__ = (
        Index('idx_ukeoi_status', 'status'),
        Index('idx_ukeoi_emp_num', 'employee_num'),
    )

    def __repr__(self):
        return f"<UkeoiEmployee(id={self.id}, emp_num={self.employee_num}, name={self.name})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        return {
            'id': self.id,
            'status': self.status,
            'employee_num': self.employee_num,
            'contract_business': self.contract_business,
            'name': self.name,
            'kana': self.kana,
            'gender': self.gender,
            'nationality': self.nationality,
            'birth_date': self.birth_date,
            'age': self.age,
            'hourly_wage': self.hourly_wage,
            'wage_revision': self.wage_revision,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
