"""StaffEmployee Repository - Office Staff Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from orm.models.staff_employee import StaffEmployee
from repositories.base_repository import BaseRepository


class StaffRepository(BaseRepository[StaffEmployee]):
    """Repository for staff (office) employees."""

    def __init__(self, session: Session):
        super().__init__(session, StaffEmployee)

    def get_by_employee_num(self, employee_num: str) -> Optional[StaffEmployee]:
        """Get by employee number."""
        return self.session.query(StaffEmployee).filter(
            StaffEmployee.employee_num == employee_num
        ).first()

    def get_active(self, skip: int = 0, limit: int = 100) -> List[StaffEmployee]:
        """Get active employees."""
        return self.session.query(StaffEmployee).filter(
            StaffEmployee.status == '在職中'
        ).offset(skip).limit(limit).all()

    def get_by_office(self, office: str) -> List[StaffEmployee]:
        """Get employees by office."""
        return self.session.query(StaffEmployee).filter(
            StaffEmployee.office == office
        ).all()
