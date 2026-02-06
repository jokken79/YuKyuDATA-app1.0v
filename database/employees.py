from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy import func, and_, distinct
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
                'after_expiry': emp.get('afterExpiry', 0.0),
                'usage_rate': emp.get('usageRate', 0.0),
                'grant_date': emp.get('grantDate'),
                'status': emp.get('status', ''),
                'kana': emp.get('kana', ''),
                'hire_date': emp.get('hireDate'),
                'updated_at': datetime.now()
            }

            # Unique key fields for conflict resolution
            key_fields = ['employee_num', 'year', 'grant_date']

            if USE_POSTGRESQL:
                stmt = pg_insert(Employee).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    constraint='uq_emp_year_grant',
                    set_={k: v for k, v in stmt_data.items() if k not in key_fields}
                )
            else:
                stmt = sqlite_insert(Employee).values(**stmt_data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=key_fields,
                    set_={k: v for k, v in stmt_data.items() if k not in key_fields}
                )

            session.execute(stmt)
        session.commit()


def save_employee_data(model_class, data: List[Dict[str, Any]]):
    """Generic function to save type-specific employee data using ORM UPSERT."""
    # Get valid column names from the ORM model
    valid_columns = {c.name for c in model_class.__table__.columns}

    with SessionLocal() as session:
        for emp in data:
            # Encrypt sensitive fields if present
            if 'birth_date' in emp:
                emp['birth_date'] = encrypt_field(emp['birth_date'])
            if 'hourly_wage' in emp:
                emp['hourly_wage'] = encrypt_field(str(emp['hourly_wage']))

            emp['updated_at'] = datetime.now()

            # Filter to only valid columns (prevents KeyError on mismatched fields)
            filtered = {k: v for k, v in emp.items() if k in valid_columns}

            if USE_POSTGRESQL:
                stmt = pg_insert(model_class).values(**filtered)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['employee_num'],
                    set_={k: v for k, v in filtered.items() if k != 'employee_num'}
                )
            else:
                stmt = sqlite_insert(model_class).values(**filtered)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['employee_num'],
                    set_={k: v for k, v in filtered.items() if k != 'employee_num'}
                )

            session.execute(stmt)
        session.commit()


def get_employees(year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve employees with their Katakana name from specific tables."""
    with SessionLocal() as session:
        # We need a join to get Kana from Genzai/Ukeoi/Staff tables
        # For simplicity and performance, we'll fetch Employees and then enrich them
        # or use a proper SQLAlchemy join query.

        from orm.models.genzai_employee import GenzaiEmployee as GenzaiEmp
        from orm.models.ukeoi_employee import UkeoiEmployee as UkeoiEmp
        from orm.models.staff_employee import StaffEmployee as StaffEmp

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
            g = session.query(GenzaiEmp.kana).filter_by(employee_num=emp.employee_num).first()
            if g:
                kana_val = g.kana
            else:
                u = session.query(UkeoiEmp.kana).filter_by(employee_num=emp.employee_num).first()
                if u:
                    kana_val = u.kana
                else:
                    s = session.query(StaffEmp.kana).filter_by(employee_num=emp.employee_num).first()
                    if s:
                        kana_val = s.kana

            emp_dict['kana'] = kana_val
            result.append(emp_dict)

        return result


def get_employees_enhanced(
    year: Optional[int] = None,
    active_only: bool = False
) -> List[Dict[str, Any]]:
    """Get employees enriched with employee_type, employment_status, is_active."""
    with SessionLocal() as session:
        query = session.query(Employee)
        if year:
            query = query.filter(Employee.year == year)

        employees = query.order_by(Employee.usage_rate.desc()).all()

        # Build lookup indexes for type classification
        genzai_map = {
            str(g.employee_num): g
            for g in session.query(GenzaiEmployee).all()
        }
        ukeoi_map = {
            str(u.employee_num): u
            for u in session.query(UkeoiEmployee).all()
        }
        staff_map = {
            str(s.employee_num): s
            for s in session.query(StaffEmployee).all()
        }

        result = []
        for emp in employees:
            emp_dict = emp.to_dict()
            emp_num = str(emp.employee_num)

            if emp_num in genzai_map:
                g = genzai_map[emp_num]
                emp_dict['employee_type'] = 'genzai'
                emp_dict['employment_status'] = g.status or ''
                emp_dict['kana'] = g.kana or ''
            elif emp_num in ukeoi_map:
                u = ukeoi_map[emp_num]
                emp_dict['employee_type'] = 'ukeoi'
                emp_dict['employment_status'] = u.status or ''
                emp_dict['kana'] = u.kana or ''
            elif emp_num in staff_map:
                s = staff_map[emp_num]
                emp_dict['employee_type'] = 'staff'
                emp_dict['employment_status'] = s.status or ''
                emp_dict['kana'] = s.kana or ''
            else:
                emp_dict['employee_type'] = 'unknown'
                emp_dict['employment_status'] = ''
                emp_dict['kana'] = ''

            emp_dict['is_active'] = emp_dict['employment_status'] == '在職中'

            if active_only and not emp_dict['is_active']:
                continue

            result.append(emp_dict)

        return result


def get_available_years() -> List[int]:
    """Get distinct years available in the employees table."""
    with SessionLocal() as session:
        rows = session.query(distinct(Employee.year)).order_by(
            Employee.year.desc()
        ).all()
        return [row[0] for row in rows if row[0] is not None]


def get_employee_by_num_year(
    employee_num: str,
    year: int
) -> Optional[Dict[str, Any]]:
    """Get a specific employee record by employee_num and year."""
    with SessionLocal() as session:
        emp = session.query(Employee).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year == year
            )
        ).first()
        return emp.to_dict() if emp else None


def update_employee(
    employee_num: str,
    year: int,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update specific fields of an employee record."""
    with SessionLocal() as session:
        emp = session.query(Employee).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year == year
            )
        ).first()
        if not emp:
            return None

        for key, value in updates.items():
            if hasattr(emp, key):
                setattr(emp, key, value)

        # Recalculate balance if granted or used changed
        if 'granted' in updates or 'used' in updates:
            emp.balance = (emp.granted or 0) - (emp.used or 0)
            if emp.granted and emp.granted > 0:
                emp.usage_rate = round((emp.used or 0) / emp.granted * 100, 1)

        emp.updated_at = datetime.now()
        session.commit()
        session.refresh(emp)
        return emp.to_dict()


def reset_employees():
    """Delete all employee vacation records."""
    with SessionLocal() as session:
        session.query(Employee).delete()
        session.commit()


def get_employee_yukyu_history(
    employee_num: str,
    current_year: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Get employee vacation history (current year and previous year)."""
    if current_year is None:
        current_year = datetime.now().year

    with SessionLocal() as session:
        records = session.query(Employee).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year.in_([current_year, current_year - 1])
            )
        ).order_by(Employee.year.desc(), Employee.grant_date).all()
        return [r.to_dict() for r in records]


def get_employee_total_balance(employee_num: str, year: int) -> float:
    """Get total vacation balance for an employee in a specific year."""
    with SessionLocal() as session:
        result = session.query(func.sum(Employee.balance)).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year == year
            )
        ).scalar()
        return float(result) if result else 0.0


def get_employee_usage_summary(
    employee_num: str,
    year: int
) -> Optional[Dict[str, Any]]:
    """Get vacation usage summary for a specific employee."""
    with SessionLocal() as session:
        records = session.query(Employee).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year == year
            )
        ).all()
        if not records:
            return None

        total_granted = sum(r.granted or 0 for r in records)
        total_used = sum(r.used or 0 for r in records)
        total_balance = sum(r.balance or 0 for r in records)
        total_expired = sum(r.expired or 0 for r in records)

        return {
            'employee_num': employee_num,
            'year': year,
            'name': records[0].name,
            'granted': total_granted,
            'used': total_used,
            'balance': total_balance,
            'expired': total_expired,
            'usage_rate': round(total_used / total_granted * 100, 1) if total_granted > 0 else 0,
        }


def get_employee_hourly_wage(employee_num: str) -> float:
    """Get hourly wage from genzai or ukeoi tables."""
    with SessionLocal() as session:
        g = session.query(GenzaiEmployee.hourly_wage).filter_by(
            employee_num=employee_num
        ).first()
        if g and g.hourly_wage:
            return float(g.hourly_wage)

        u = session.query(UkeoiEmployee.hourly_wage).filter_by(
            employee_num=employee_num
        ).first()
        if u and u.hourly_wage:
            return float(u.hourly_wage)

        return 0.0


def recalculate_employee_from_details(
    employee_num: str,
    year: int
) -> Optional[Dict[str, Any]]:
    """Recalculate employee totals from usage details."""
    from orm import YukyuUsageDetail

    with SessionLocal() as session:
        emp = session.query(Employee).filter(
            and_(
                Employee.employee_num == employee_num,
                Employee.year == year
            )
        ).first()
        if not emp:
            return None

        total_used = session.query(func.sum(YukyuUsageDetail.days_used)).filter(
            and_(
                YukyuUsageDetail.employee_num == employee_num,
                YukyuUsageDetail.year == year
            )
        ).scalar() or 0.0

        emp.used = float(total_used)
        emp.balance = (emp.granted or 0) - emp.used
        if emp.granted and emp.granted > 0:
            emp.usage_rate = round(emp.used / emp.granted * 100, 1)
        emp.updated_at = datetime.now()

        session.commit()
        session.refresh(emp)
        return emp.to_dict()


def bulk_update_employees(
    employee_nums: List[str],
    year: int,
    updates: Dict[str, Any],
    updated_by: str = 'system',
    validate_limit: bool = True
) -> Dict[str, Any]:
    """Bulk update multiple employees in one operation."""
    operation_id = str(uuid.uuid4())[:8]
    updated_count = 0
    errors = []
    warnings = []

    with SessionLocal() as session:
        for emp_num in employee_nums:
            emp = session.query(Employee).filter(
                and_(
                    Employee.employee_num == emp_num,
                    Employee.year == year
                )
            ).first()
            if not emp:
                errors.append(f"Employee {emp_num} not found for year {year}")
                continue

            old_granted = emp.granted or 0
            old_used = emp.used or 0

            if 'add_granted' in updates:
                emp.granted = old_granted + updates['add_granted']
            if 'add_used' in updates:
                emp.used = old_used + updates['add_used']
            if 'set_granted' in updates:
                emp.granted = updates['set_granted']
            if 'set_used' in updates:
                emp.used = updates['set_used']
            if 'set_haken' in updates:
                emp.haken = updates['set_haken']

            emp.balance = (emp.granted or 0) - (emp.used or 0)
            if emp.granted and emp.granted > 0:
                emp.usage_rate = round((emp.used or 0) / emp.granted * 100, 1)

            if validate_limit and emp.balance < 0:
                warnings.append({
                    'employee_num': emp_num,
                    'message': f'Negative balance: {emp.balance}'
                })

            emp.updated_at = datetime.now()
            updated_count += 1

        session.commit()

    return {
        'success': len(errors) == 0,
        'operation_id': operation_id,
        'updated_count': updated_count,
        'errors': errors,
        'warnings': warnings,
    }


def get_bulk_update_history(
    operation_id: Optional[str] = None,
    employee_num: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get bulk update operation history from audit log."""
    from orm import AuditLog

    with SessionLocal() as session:
        query = session.query(AuditLog).filter(
            AuditLog.action == 'BULK_UPDATE'
        )
        if operation_id:
            query = query.filter(
                AuditLog.additional_info.contains(operation_id)
            )
        if employee_num:
            query = query.filter(AuditLog.entity_id.contains(employee_num))

        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]


def revert_bulk_update(
    operation_id: str,
    reverted_by: str = 'system'
) -> Dict[str, Any]:
    """Revert a bulk update operation (placeholder - needs audit trail)."""
    return {
        'success': True,
        'reverted_count': 0,
        'errors': [],
        'reverted_at': datetime.now().isoformat(),
        'message': 'Revert requires audit trail records for the operation'
    }
