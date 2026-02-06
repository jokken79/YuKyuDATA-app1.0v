from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from orm import SessionLocal, LeaveRequest, YukyuUsageDetail
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
            requested_at=data.get('requested_at') or datetime.now().isoformat(),
            year=data.get('year'),
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
                'updated_at': datetime.now()
            }

            if USE_POSTGRESQL:
                stmt = pg_insert(YukyuUsageDetail).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['employee_num', 'use_date'],
                    set_={k: v for k, v in stmt_data.items() if k not in ['employee_num', 'use_date']}
                )
            else:
                stmt = sqlite_insert(YukyuUsageDetail).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['employee_num', 'use_date'],
                    set_={k: v for k, v in stmt_data.items() if k not in ['employee_num', 'use_date']}
                )
            
            session.execute(stmt)
        session.commit()
