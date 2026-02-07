from typing import Dict, Any, List
from sqlalchemy import func, and_
from orm import SessionLocal, Employee, LeaveRequest, GenzaiEmployee, UkeoiEmployee, StaffEmployee


def get_dashboard_stats(year: int) -> Dict[str, Any]:
    """Calculate dashboard KPIs using ORM."""
    with SessionLocal() as session:
        # Total employees in specific year
        total_employees = session.query(func.count(Employee.id)).filter(
            Employee.year == year
        ).scalar() or 0

        # Total active (matching records in type tables)
        # Note: In our system, Employees are only for active-for-yukyu

        # Average usage rate
        avg_usage = session.query(func.avg(Employee.usage_rate)).filter(
            Employee.year == year
        ).scalar() or 0.0

        # Compliance check (>= 5 days used)
        compliant = session.query(func.count(Employee.id)).filter(
            and_(Employee.year == year, Employee.used >= 5)
        ).scalar() or 0

        # Pending requests
        pending_requests = session.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.status == 'PENDING'
        ).scalar() or 0

        return {
            'total_employees': total_employees,
            'average_usage_rate': round(float(avg_usage), 1),
            'compliant_count': compliant,
            'non_compliant_count': max(0, total_employees - compliant),
            'pending_requests': pending_requests,
            'year': year
        }


def get_workplace_distribution(year: int) -> List[Dict[str, Any]]:
    """Get employee counts by workplace (haken)."""
    with SessionLocal() as session:
        results = session.query(
            Employee.haken,
            func.count(Employee.id)
        ).filter(
            Employee.year == year
        ).group_by(Employee.haken).all()

        return [{'name': h or 'Unknown', 'value': count} for h, count in results]


def get_employee_type_distribution() -> Dict[str, int]:
    """Get counts by employee category."""
    with SessionLocal() as session:
        return {
            'genzai': session.query(func.count(GenzaiEmployee.id)).scalar() or 0,
            'ukeoi': session.query(func.count(UkeoiEmployee.id)).scalar() or 0,
            'staff': session.query(func.count(StaffEmployee.id)).scalar() or 0
        }
