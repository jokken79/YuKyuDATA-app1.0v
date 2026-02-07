from typing import List, Optional, Dict, Any
from orm import SessionLocal, GenzaiEmployee
from .employees import save_employee_data


def get_genzai(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """Get dispatch employees (genzai) with optional filters."""
    with SessionLocal() as session:
        query = session.query(GenzaiEmployee)

        if status:
            query = query.filter(GenzaiEmployee.status == status)

        employees = query.order_by(GenzaiEmployee.employee_num).all()
        return [emp.to_dict() for emp in employees]


def save_genzai(data: List[Dict[str, Any]]):
    """Save genzai employees using generic save_employee_data."""
    save_employee_data(GenzaiEmployee, data)


def reset_genzai():
    """Delete all genzai employee records."""
    with SessionLocal() as session:
        session.query(GenzaiEmployee).delete()
        session.commit()
