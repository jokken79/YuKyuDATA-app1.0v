"""GenzaiEmployee Repository - Dispatch Employee Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from orm.models.genzai_employee import GenzaiEmployee
from repositories.base_repository import BaseRepository


class GenzaiRepository(BaseRepository[GenzaiEmployee]):
    """Repository for Genzai (dispatch) employees."""

    def __init__(self, session: Session):
        super().__init__(session, GenzaiEmployee)

    def get_by_employee_num(self, employee_num: str) -> Optional[GenzaiEmployee]:
        """Get by employee number."""
        return self.session.query(GenzaiEmployee).filter(
            GenzaiEmployee.employee_num == employee_num
        ).first()

    def get_active(self, skip: int = 0, limit: int = 100) -> List[GenzaiEmployee]:
        """Get active employees (在職中)."""
        return self.session.query(GenzaiEmployee).filter(
            GenzaiEmployee.status == '在職中'
        ).offset(skip).limit(limit).all()

    def get_by_dispatch(self, dispatch_id: str, skip: int = 0, limit: int = 100) -> List[GenzaiEmployee]:
        """Get employees by dispatch."""
        return self.session.query(GenzaiEmployee).filter(
            GenzaiEmployee.dispatch_id == dispatch_id
        ).offset(skip).limit(limit).all()

    def search_by_name(self, name: str) -> List[GenzaiEmployee]:
        """Search by name."""
        return self.session.query(GenzaiEmployee).filter(
            GenzaiEmployee.name.ilike(f'%{name}%')
        ).all()

    def get_by_department(self, department: str) -> List[GenzaiEmployee]:
        """Get employees by department."""
        return self.session.query(GenzaiEmployee).filter(
            GenzaiEmployee.department == department
        ).all()
