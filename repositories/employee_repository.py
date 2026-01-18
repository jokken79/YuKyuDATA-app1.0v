"""Employee Repository - Vacation Data Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from orm.models.employee import Employee
from repositories.base_repository import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    """
    Repository for Employee (vacation data) operations.

    Provides specialized queries for vacation management:
    - Get employees by year
    - Search by employee number
    - Find employees with low balance
    - Find expiring days
    """

    def __init__(self, session: Session):
        super().__init__(session, Employee)

    def get_by_employee_and_year(
        self,
        employee_num: str,
        year: int
    ) -> Optional[Employee]:
        """Get employee record for specific year."""
        return self.session.query(Employee).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year == year
            )
        ).first()

    def get_by_year(self, year: int, skip: int = 0, limit: int = 100) -> List[Employee]:
        """Get all employees for a given year."""
        return self.session.query(Employee).filter(
            Employee.year == year
        ).offset(skip).limit(limit).all()

    def get_by_year_count(self, year: int) -> int:
        """Count employees in a given year."""
        return self.session.query(Employee).filter(
            Employee.year == year
        ).count()

    def get_by_employee_num(self, employee_num: str, skip: int = 0, limit: int = 100) -> List[Employee]:
        """Get all years for a given employee."""
        return self.session.query(Employee).filter(
            Employee.employee_num == employee_num
        ).order_by(Employee.year.desc()).offset(skip).limit(limit).all()

    def search_by_name(self, name: str, year: Optional[int] = None) -> List[Employee]:
        """Search employees by name."""
        query = self.session.query(Employee).filter(
            Employee.name.ilike(f'%{name}%')
        )

        if year:
            query = query.filter(Employee.year == year)

        return query.all()

    def get_low_balance(
        self,
        year: int,
        threshold: float = 5.0,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees with balance below threshold."""
        return self.session.query(Employee).filter(
            and_(
                Employee.year == year,
                Employee.balance < threshold
            )
        ).offset(skip).limit(limit).all()

    def get_expiring_soon(
        self,
        year: int,
        threshold_days: float = 10.0,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """
        Get employees with days that will expire soon.

        Note: This is a simple heuristic. Actual expiration logic
        should be in fiscal_year.py service.
        """
        return self.session.query(Employee).filter(
            and_(
                Employee.year == year,
                Employee.balance < threshold_days
            )
        ).offset(skip).limit(limit).all()

    def get_high_usage(
        self,
        year: int,
        min_usage_rate: float = 80.0,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees with high usage rate."""
        return self.session.query(Employee).filter(
            and_(
                Employee.year == year,
                Employee.usage_rate >= min_usage_rate
            )
        ).offset(skip).limit(limit).all()

    def get_by_haken(
        self,
        haken: str,
        year: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees by workplace/dispatch location."""
        return self.session.query(Employee).filter(
            and_(
                Employee.haken == haken,
                Employee.year == year
            )
        ).offset(skip).limit(limit).all()

    def bulk_upsert(self, employees: List[dict]) -> int:
        """
        Bulk insert or update employees.

        Args:
            employees: List of employee dicts with keys:
                      employee_num, year, name, granted, used, balance, expired, etc.

        Returns:
            Number of rows affected
        """
        upserted = 0

        for emp_data in employees:
            employee_num = emp_data.get('employee_num')
            year = emp_data.get('year')

            existing = self.get_by_employee_and_year(employee_num, year)

            if existing:
                # Update
                for key, value in emp_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                # Create
                new_emp = Employee(**emp_data)
                self.session.add(new_emp)

            upserted += 1

        self.session.flush()
        return upserted

    def get_latest_year(self) -> Optional[int]:
        """Get the latest year with employee data."""
        result = self.session.query(
            self.session.query(Employee.year).distinct().order_by(Employee.year.desc()).limit(1).scalar()
        ).scalar()
        return result

    def delete_by_year(self, year: int) -> int:
        """Delete all employees for a given year."""
        count = self.session.query(Employee).filter(
            Employee.year == year
        ).delete()
        self.session.flush()
        return count
