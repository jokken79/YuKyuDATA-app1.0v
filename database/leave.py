from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import and_
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from orm import SessionLocal, LeaveRequest, YukyuUsageDetail, Employee
from .connection import USE_POSTGRESQL

def save_leave_request(data: Dict[str, Any]) -> int:
    """Save a leave request using ORM."""
    with SessionLocal() as session:
        leave_req = LeaveRequest(
            employee_num=data.get('employee_num'),
            employee_name=data.get('employee_name'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            days_requested=data.get('days_requested'),
            hours_requested=data.get('hours_requested', 0.0),
            leave_type=data.get('leave_type', 'full'),
            reason=data.get('reason'),
            status=data.get('status', 'PENDING'),
            year=data.get('year'),
            hourly_wage=data.get('hourly_wage'),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(leave_req)
        session.commit()
        session.refresh(leave_req)
        return leave_req.id

def get_leave_requests(status: Optional[str] = None, employee_num: Optional[str] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve leave requests using ORM."""
    with SessionLocal() as session:
        query = session.query(LeaveRequest)
        
        if status:
            query = query.filter(LeaveRequest.status == status)
        if employee_num:
            query = query.filter(LeaveRequest.employee_num == employee_num)
        if year:
            query = query.filter(LeaveRequest.year == year)
            
        requests = query.order_by(LeaveRequest.created_at.desc()).all()
        return [req.to_dict() for req in requests]

def save_yukyu_usage_details(usage_details_list: List[Dict[str, Any]]):
    """Saves yukyu usage details using ORM UPSERT logic."""
    with SessionLocal() as session:
        for detail in usage_details_list:
            stmt_data = {
                'employee_num': detail.get('employee_num'),
                'name': detail.get('name'),
                'use_date': detail.get('use_date'),
                'year': detail.get('year'),
                'month': detail.get('month'),
                'days_used': detail.get('days_used', 1.0),
                'leave_type': detail.get('leave_type', 'full'),
                'source': 'excel',
                'updated_at': datetime.now()
            }

            key_fields = ['employee_num', 'use_date']

            if USE_POSTGRESQL:
                stmt = pg_insert(YukyuUsageDetail).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=key_fields,
                    set_={k: v for k, v in stmt_data.items() if k not in key_fields}
                )
            else:
                stmt = sqlite_insert(YukyuUsageDetail).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=key_fields,
                    set_={k: v for k, v in stmt_data.items() if k not in key_fields}
                )

            session.execute(stmt)
        session.commit()


def create_leave_request(
    employee_num: str,
    employee_name: str,
    start_date: str,
    end_date: str,
    days_requested: float,
    reason: str,
    year: int,
    hours_requested: float = 0,
    leave_type: str = 'full',
    hourly_wage: float = 0
) -> str:
    """Create a new leave request with explicit parameters."""
    with SessionLocal() as session:
        leave_req = LeaveRequest(
            employee_num=employee_num,
            employee_name=employee_name,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            hours_requested=hours_requested,
            leave_type=leave_type,
            reason=reason,
            status='PENDING',
            year=year,
            hourly_wage=hourly_wage,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(leave_req)
        session.commit()
        session.refresh(leave_req)
        return leave_req.id


def approve_leave_request(request_id, approved_by: str) -> bool:
    """Approve a leave request and deduct days from employee balance."""
    with SessionLocal() as session:
        leave_req = session.query(LeaveRequest).filter(
            LeaveRequest.id == str(request_id)
        ).first()
        if not leave_req:
            raise ValueError(f"Leave request {request_id} not found")
        if leave_req.status != 'PENDING':
            raise ValueError(f"Leave request {request_id} is not PENDING (current: {leave_req.status})")

        leave_req.status = 'APPROVED'
        leave_req.approver = approved_by
        leave_req.approved_at = datetime.now()
        leave_req.updated_at = datetime.now()

        # Deduct days from employee balance (simple deduction from first matching record)
        emp = session.query(Employee).filter(
            and_(
                Employee.employee_num == leave_req.employee_num,
                Employee.year == leave_req.year
            )
        ).order_by(Employee.grant_date.desc()).first()

        if emp:
            emp.used = (emp.used or 0) + leave_req.days_requested
            emp.balance = (emp.granted or 0) - emp.used
            if emp.granted and emp.granted > 0:
                emp.usage_rate = round(emp.used / emp.granted * 100, 1)
            emp.updated_at = datetime.now()

        session.commit()
        return True


def reject_leave_request(request_id, rejected_by: str) -> bool:
    """Reject a leave request (no balance changes)."""
    with SessionLocal() as session:
        leave_req = session.query(LeaveRequest).filter(
            LeaveRequest.id == str(request_id)
        ).first()
        if not leave_req:
            raise ValueError(f"Leave request {request_id} not found")
        if leave_req.status != 'PENDING':
            raise ValueError(f"Leave request {request_id} is not PENDING (current: {leave_req.status})")

        leave_req.status = 'REJECTED'
        leave_req.approver = rejected_by
        leave_req.approved_at = datetime.now()
        leave_req.updated_at = datetime.now()

        session.commit()
        return True


def cancel_leave_request(request_id) -> Dict[str, Any]:
    """Cancel a PENDING leave request (delete it)."""
    with SessionLocal() as session:
        leave_req = session.query(LeaveRequest).filter(
            LeaveRequest.id == str(request_id)
        ).first()
        if not leave_req:
            raise ValueError(f"Leave request {request_id} not found")
        if leave_req.status != 'PENDING':
            raise ValueError(f"Only PENDING requests can be cancelled (current: {leave_req.status})")

        result = leave_req.to_dict()
        session.delete(leave_req)
        session.commit()
        return result


def validate_balance_limit(employee_num: str, year: int):
    """Validate that employee balance does not exceed 40 days."""
    from sqlalchemy import func

    with SessionLocal() as session:
        total_balance = session.query(func.sum(Employee.balance)).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year == year
            )
        ).scalar() or 0

        if total_balance > 40:
            raise ValueError(f"Balance exceeds 40 days limit: {total_balance}")


def revert_approved_request(request_id, reverted_by: str) -> Dict[str, Any]:
    """Revert an APPROVED leave request, returning days to employee balance."""
    with SessionLocal() as session:
        leave_req = session.query(LeaveRequest).filter(
            LeaveRequest.id == str(request_id)
        ).first()
        if not leave_req:
            raise ValueError(f"Leave request {request_id} not found")
        if leave_req.status != 'APPROVED':
            raise ValueError(f"Only APPROVED requests can be reverted (current: {leave_req.status})")

        days_returned = leave_req.days_requested

        # Return days to employee balance
        emp = session.query(Employee).filter(
            and_(
                Employee.employee_num == leave_req.employee_num,
                Employee.year == leave_req.year
            )
        ).order_by(Employee.grant_date.desc()).first()

        if emp:
            emp.used = max(0, (emp.used or 0) - days_returned)
            emp.balance = (emp.granted or 0) - emp.used
            if emp.granted and emp.granted > 0:
                emp.usage_rate = round(emp.used / emp.granted * 100, 1)
            emp.updated_at = datetime.now()

        leave_req.status = 'CANCELLED'
        leave_req.approver = reverted_by
        leave_req.updated_at = datetime.now()

        session.commit()

        return {
            'request_id': leave_req.id,
            'days_returned': days_returned,
            'reverted_by': reverted_by,
            'new_status': 'CANCELLED'
        }
