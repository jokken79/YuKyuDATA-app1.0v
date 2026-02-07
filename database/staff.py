from typing import List, Optional, Dict, Any
from orm import SessionLocal, StaffEmployee
from .employees import save_employee_data


def get_staff(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """Get office staff employees with optional filters."""
    with SessionLocal() as session:
        query = session.query(StaffEmployee)

        if status:
            query = query.filter(StaffEmployee.status == status)

        employees = query.order_by(StaffEmployee.employee_num).all()
        return [emp.to_dict() for emp in employees]


def save_staff(data: List[Dict[str, Any]]):
    """Save staff employees using generic save_employee_data."""
    save_employee_data(StaffEmployee, data)


def reset_staff():
    """Delete all staff employee records."""
    with SessionLocal() as session:
        session.query(StaffEmployee).delete()
        session.commit()
