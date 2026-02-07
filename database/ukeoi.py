from typing import List, Optional, Dict, Any
from orm import SessionLocal, UkeoiEmployee
from .employees import save_employee_data


def get_ukeoi(
    status: Optional[str] = None,
    year: Optional[int] = None,
    active_in_year: bool = False
) -> List[Dict[str, Any]]:
    """Get contract employees (ukeoi) with optional filters."""
    with SessionLocal() as session:
        query = session.query(UkeoiEmployee)

        if status:
            query = query.filter(UkeoiEmployee.status == status)

        employees = query.order_by(UkeoiEmployee.employee_num).all()
        return [emp.to_dict() for emp in employees]


def save_ukeoi(data: List[Dict[str, Any]]):
    """Save ukeoi employees using generic save_employee_data."""
    save_employee_data(UkeoiEmployee, data)


def reset_ukeoi():
    """Delete all ukeoi employee records."""
    with SessionLocal() as session:
        session.query(UkeoiEmployee).delete()
        session.commit()
