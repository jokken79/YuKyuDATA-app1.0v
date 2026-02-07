"""YukyuUsageDetail Repository - Individual Leave Date Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from orm.models.yukyu_usage_detail import YukyuUsageDetail
from repositories.base_repository import BaseRepository


class YukyuUsageDetailRepository(BaseRepository[YukyuUsageDetail]):
    """Repository for individual leave usage details."""

    def __init__(self, session: Session):
        super().__init__(session, YukyuUsageDetail)

    def get_by_employee_and_year(
        self,
        employee_num: str,
        year: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[YukyuUsageDetail]:
        """Get all usage details for employee in year."""
        return self.session.query(YukyuUsageDetail).filter(
            and_(
                YukyuUsageDetail.employee_num == employee_num,
                YukyuUsageDetail.year == year
            )
        ).order_by(YukyuUsageDetail.use_date).offset(skip).limit(limit).all()

    def get_by_date_range(
        self,
        employee_num: str,
        year: int,
        start_date: str,
        end_date: str
    ) -> List[YukyuUsageDetail]:
        """Get usage details for date range."""
        return self.session.query(YukyuUsageDetail).filter(
            and_(
                YukyuUsageDetail.employee_num == employee_num,
                YukyuUsageDetail.year == year,
                YukyuUsageDetail.use_date >= start_date,
                YukyuUsageDetail.use_date <= end_date
            )
        ).order_by(YukyuUsageDetail.use_date).all()

    def get_total_days_used(
        self,
        employee_num: str,
        year: int
    ) -> float:
        """Calculate total days used."""
        result = self.session.query(
            self.session.func.sum(YukyuUsageDetail.days_used)
        ).filter(
            and_(
                YukyuUsageDetail.employee_num == employee_num,
                YukyuUsageDetail.year == year
            )
        ).scalar()

        return result or 0.0

    def delete_by_employee_and_year(self, employee_num: str, year: int) -> int:
        """Delete all usage details for employee in year."""
        count = self.session.query(YukyuUsageDetail).filter(
            and_(
                YukyuUsageDetail.employee_num == employee_num,
                YukyuUsageDetail.year == year
            )
        ).delete()
        self.session.flush()
        return count
