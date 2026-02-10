"""LeaveRequest Repository - Leave Request Workflow Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from orm.models.leave_request import LeaveRequest, LeaveStatus
from repositories.base_repository import BaseRepository


class LeaveRequestRepository(BaseRepository[LeaveRequest]):
    """
    Repository for LeaveRequest operations.

    Provides specialized queries for leave request workflow:
    - Get pending requests
    - Get approved/rejected requests
    - Get by employee
    - Get by date range
    """

    def __init__(self, session: Session):
        super().__init__(session, LeaveRequest)

    def get_by_status(
        self,
        status: str,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LeaveRequest]:
        """Get requests by status."""
        query = self.session.query(LeaveRequest).filter(
            LeaveRequest.status == status
        )

        if year:
            query = query.filter(LeaveRequest.year == year)

        return query.offset(skip).limit(limit).all()

    def get_by_employee(
        self,
        employee_num: str,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LeaveRequest]:
        """Get all requests by employee."""
        query = self.session.query(LeaveRequest).filter(
            LeaveRequest.employee_num == employee_num
        )

        if year:
            query = query.filter(LeaveRequest.year == year)

        return query.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_date_range(
        self,
        start_date: str,
        end_date: str,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LeaveRequest]:
        """Get requests within date range."""
        query = self.session.query(LeaveRequest).filter(
            and_(
                LeaveRequest.start_date >= start_date,
                LeaveRequest.end_date <= end_date
            )
        )

        if year:
            query = query.filter(LeaveRequest.year == year)

        return query.offset(skip).limit(limit).all()

    def get_pending(self, year: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[LeaveRequest]:
        """Get pending requests."""
        return self.get_by_status(LeaveStatus.PENDING, year, skip, limit)

    def get_approved(self, year: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[LeaveRequest]:
        """Get approved requests."""
        return self.get_by_status(LeaveStatus.APPROVED, year, skip, limit)

    def get_rejected(self, year: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[LeaveRequest]:
        """Get rejected requests."""
        return self.get_by_status(LeaveStatus.REJECTED, year, skip, limit)

    def count_by_status(self, status: str, year: Optional[int] = None) -> int:
        """Count requests by status."""
        query = self.session.query(LeaveRequest).filter(
            LeaveRequest.status == status
        )

        if year:
            query = query.filter(LeaveRequest.year == year)

        return query.count()

    def get_by_employee_and_status(
        self,
        employee_num: str,
        status: str,
        year: Optional[int] = None
    ) -> List[LeaveRequest]:
        """Get requests by employee and status."""
        query = self.session.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_num == employee_num,
                LeaveRequest.status == status
            )
        )

        if year:
            query = query.filter(LeaveRequest.year == year)

        return query.all()

    def approve(self, id: str, approver: str) -> Optional[LeaveRequest]:
        """Approve a leave request."""
        from datetime import datetime, timezone
        request = self.get_by_id(id)
        if request:
            request.status = LeaveStatus.APPROVED
            request.approver = approver
            request.approved_at = datetime.now(timezone.utc)
            self.session.flush()
        return request

    def reject(self, id: str, approver: str) -> Optional[LeaveRequest]:
        """Reject a leave request."""
        from datetime import datetime, timezone
        request = self.get_by_id(id)
        if request:
            request.status = LeaveStatus.REJECTED
            request.approver = approver
            request.approved_at = datetime.now(timezone.utc)
            self.session.flush()
        return request

    def get_overlapping(
        self,
        employee_num: str,
        start_date: str,
        end_date: str,
        year: int,
        exclude_id: Optional[str] = None
    ) -> List[LeaveRequest]:
        """Get overlapping leave requests for same employee."""
        query = self.session.query(LeaveRequest).filter(
            and_(
                LeaveRequest.employee_num == employee_num,
                LeaveRequest.year == year,
                LeaveRequest.status == LeaveStatus.APPROVED,
                # Date range overlap logic
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date
            )
        )

        if exclude_id:
            query = query.filter(LeaveRequest.id != exclude_id)

        return query.all()
