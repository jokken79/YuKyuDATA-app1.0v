"""StaffEmployee ORM Model - Office Staff"""

from sqlalchemy import Column, String, Float, Integer, Index
from orm.models.base import Base, BaseModel


class StaffEmployee(BaseModel, Base):
    """
    Office staff employee data.

    Similar structure to GenzaiEmployee but for office staff.
    """

    __tablename__ = "staff"

    status = Column(String(20))  # 在職中, 退職
    employee_num = Column(String(12), unique=True, index=True)
    office = Column(String(100))  # 事務所
    name = Column(String(100))
    kana = Column(String(100))
    gender = Column(String(10))
    nationality = Column(String(50))
    birth_date = Column(String(10))  # YYYY-MM-DD
    age = Column(Integer)
    visa_expiry = Column(String(10))  # YYYY-MM-DD ビザ期限
    visa_type = Column(String(50))  # ビザ種類
    spouse = Column(String(20))  # 配偶者
    postal_code = Column(String(10))  # 〒
    address = Column(String(200))  # 住所
    building = Column(String(100))  # 建物名
    hire_date = Column(String(10))  # YYYY-MM-DD 入社日
    leave_date = Column(String(10))  # YYYY-MM-DD 退社日

    __table_args__ = (
        Index('idx_staff_status', 'status'),
        Index('idx_staff_emp_num', 'employee_num'),
    )

    def __repr__(self):
        return f"<StaffEmployee(id={self.id}, emp_num={self.employee_num}, name={self.name})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        return {
            'id': self.id,
            'status': self.status,
            'employee_num': self.employee_num,
            'office': self.office,
            'name': self.name,
            'kana': self.kana,
            'gender': self.gender,
            'nationality': self.nationality,
            'birth_date': self.birth_date,
            'age': self.age,
            'visa_expiry': self.visa_expiry,
            'visa_type': self.visa_type,
            'spouse': self.spouse,
            'postal_code': self.postal_code,
            'address': self.address,
            'building': self.building,
            'hire_date': self.hire_date,
            'leave_date': self.leave_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
