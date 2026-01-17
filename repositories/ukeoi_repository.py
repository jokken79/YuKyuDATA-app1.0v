"""UkeoiEmployee Repository - Contract Employee Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from orm.models.ukeoi_employee import UkeoiEmployee
from repositories.base_repository import BaseRepository


class UkeoiRepository(BaseRepository[UkeoiEmployee]):
    """Repository for Ukeoi (contract) employees."""

    def __init__(self, session: Session):
        super().__init__(session, UkeoiEmployee)

    def get_by_employee_num(self, employee_num: str) -> Optional[UkeoiEmployee]:
        """Get by employee number."""
        return self.session.query(UkeoiEmployee).filter(
            UkeoiEmployee.employee_num == employee_num
        ).first()

    def get_active(self, skip: int = 0, limit: int = 100) -> List[UkeoiEmployee]:
        """Get active employees."""
        return self.session.query(UkeoiEmployee).filter(
            UkeoiEmployee.status == '在職中'
        ).offset(skip).limit(limit).all()

    def get_by_dispatch(self, dispatch_id: str) -> List[UkeoiEmployee]:
        """Get employees by dispatch."""
        return self.session.query(UkeoiEmployee).filter(
            UkeoiEmployee.dispatch_id == dispatch_id
        ).all()
