from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from orm import SessionLocal, Employee, GenzaiEmployee, UkeoiEmployee, StaffEmployee
from .connection import USE_POSTGRESQL
from services.crypto_utils import encrypt_field

def save_employees(employees_data: List[Dict[str, Any]]):
    """Saves vacation data (employees table) using ORM UPSERT logic."""
    with SessionLocal() as session:
        for emp in employees_data:
            # Prepare data for UPSERT
            stmt_data = {
                'employee_num': emp.get('employeeNum'),
                'year': emp.get('year'),
                'name': emp.get('name'),
                'haken': emp.get('haken'),
                'granted': emp.get('granted', 0.0),
                'used': emp.get('used', 0.0),
                'balance': emp.get('balance', 0.0),
                'expired': emp.get('expired', 0.0),
                'usage_rate': emp.get('usageRate', 0.0),
                'updated_at': datetime.now()
            }

            if USE_POSTGRESQL:
                stmt = pg_insert(Employee).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    constraint='uq_emp_year',
                    set_={k: v for k, v in stmt_data.items() if k not in ['employee_num', 'year']}
                )
            else:
                stmt = sqlite_insert(Employee).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['employee_num', 'year'],
                    set_={k: v for k, v in stmt_data.items() if k not in ['employee_num', 'year']}
                )
            
            session.execute(stmt)
        session.commit()

def save_employee_data(model_class, data: List[Dict[str, Any]]):
    """Generic function to save type-specific employee data using ORM UPSERT."""
    with SessionLocal() as session:
        for emp in data:
            # Encrypt sensitive fields if present
            if 'birth_date' in emp:
                emp['birth_date'] = encrypt_field(emp['birth_date'])
            if 'hourly_wage' in emp:
                emp['hourly_wage'] = encrypt_field(str(emp['hourly_wage']))
            
            emp['updated_at'] = datetime.now()

            if USE_POSTGRESQL:
                stmt = pg_insert(model_class).values(**emp)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['employee_num'],
                    set_={k: v for k, v in emp.items() if k != 'employee_num'}
                )
            else:
                stmt = sqlite_insert(model_class).values(**emp)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['employee_num'],
                    set_={k: v for k, v in emp.items() if k != 'employee_num'}
                )
            
            session.execute(stmt)
        session.commit()

def get_employees(year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve employees with their Katakana name from specific tables."""
    with SessionLocal() as session:
        # We need a join to get Kana from Genzai/Ukeoi/Staff tables
        # For simplicity and performance, we'll fetch Employees and then enrich them
        # or use a proper SQLAlchemy join query.
        
        from sqlalchemy import or_
        from orm.models.genzai_employee import GenzaiEmployee
        from orm.models.ukeoi_employee import UkeoiEmployee
        from orm.models.staff_employee import StaffEmployee
        
        query = session.query(Employee)
        if year:
            query = query.filter(Employee.year == year)
        
        employees = query.order_by(Employee.usage_rate.desc()).all()
        
        # Enrich with Kana
        result = []
        for emp in employees:
            emp_dict = emp.to_dict()
            # Try to find kana in any of the specific tables
            # Proactive: Cache this or use a single join query for production
            kana_val = ""
            g = session.query(GenzaiEmployee.kana).filter_by(employee_num=emp.employee_num).first()
            if g: kana_val = g.kana
            else:
                u = session.query(UkeoiEmployee.kana).filter_by(employee_num=emp.employee_num).first()
                if u: kana_val = u.kana
                else:
                    s = session.query(StaffEmployee.kana).filter_by(employee_num=emp.employee_num).first()
                    if s: kana_val = s.kana
            
            emp_dict['kana'] = kana_val
            result.append(emp_dict)
            
        return result
