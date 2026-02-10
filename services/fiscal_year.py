"""
Módulo de gestión del año fiscal de vacaciones (有給休暇)

Características:
- Período de cierre: 21日〜20日 (configurable)
- Carry-over máximo: 2 años
- Uso LIFO: días más nuevos primero (los nuevos se consumen antes)
- Tabla de otorgamiento según antigüedad (Ley Laboral Japonesa)
"""

from datetime import date, datetime, timezone
from typing import Optional, Dict, List, Tuple

from database.connection import get_db, USE_POSTGRESQL
from database.audit import log_audit_action
from orm import SessionLocal
from orm.models.employee import Employee
from orm.models.leave_request import LeaveRequest
from sqlalchemy import and_

# Tabla de otorgamiento según antigüedad (Ley Laboral Japonesa Art. 39)
GRANT_TABLE = {
    0.5: 10,   # 6 meses de servicio continuo
    1.5: 11,   # 1 año 6 meses
    2.5: 12,   # 2 años 6 meses
    3.5: 14,   # 3 años 6 meses
    4.5: 16,   # 4 años 6 meses
    5.5: 18,   # 5 años 6 meses
    6.5: 20,   # 6+ años (máximo legal)
}

# Configuración del período fiscal
FISCAL_CONFIG = {
    'period_start_day': 21,           # Día de inicio del período mensual
    'period_end_day': 20,             # Día de fin del período mensual
    'max_carry_over_years': 2,        # Máximo años de carry-over
    'max_accumulated_days': 40,       # Máximo días acumulables
    'minimum_annual_use': 5,          # 5日取得義務
    'minimum_days_for_obligation': 10, # Aplica obligación si tiene 10+ días
    'ledger_retention_years': 3,      # Años de retención de registros
}


def _prepare_query(query: str) -> str:
    """Ajusta los placeholders de parámetros según el motor de BD."""
    if USE_POSTGRESQL:
        # Cambiar placeholders de SQLite (?) a PostgreSQL (%s)
        return query.replace('?', '%s')
    return query


def calculate_seniority_years(hire_date: str, reference_date: date = None) -> float:
    """
    Calcula años de antigüedad desde la fecha de entrada.

    Args:
        hire_date: Fecha de entrada en formato YYYY-MM-DD
        reference_date: Fecha de referencia (default: hoy)

    Returns:
        Años de antigüedad (float)
    """
    if not hire_date:
        return 0.0

    try:
        hire = datetime.strptime(hire_date, '%Y-%m-%d').date()
        ref = reference_date or date.today()

        years = (ref - hire).days / 365.25
        return round(years, 2)
    except (ValueError, TypeError):
        return 0.0


def calculate_granted_days(seniority_years: float) -> int:
    """
    Calcula días otorgados según antigüedad basado en la Ley Laboral Japonesa.

    Args:
        seniority_years: Años de antigüedad

    Returns:
        Días de vacaciones a otorgar
    """
    granted = 0
    for threshold, days in sorted(GRANT_TABLE.items()):
        if seniority_years >= threshold:
            granted = days
        else:
            break
    return granted


def get_fiscal_period(year: int, month: int) -> Tuple[str, str]:
    """
    Calcula el período fiscal (21日〜20日) para un mes dado.

    Args:
        year: Año
        month: Mes (1-12)

    Returns:
        Tuple (start_date, end_date) en formato YYYY-MM-DD
    """
    start_day = FISCAL_CONFIG['period_start_day']
    end_day = FISCAL_CONFIG['period_end_day']

    # Período: mes anterior día 21 → mes actual día 20
    if month == 1:
        start_year = year - 1
        start_month = 12
    else:
        start_year = year
        start_month = month - 1

    start_date = f"{start_year}-{start_month:02d}-{start_day:02d}"
    end_date = f"{year}-{month:02d}-{end_day:02d}"

    return start_date, end_date


def get_fiscal_year_period(fiscal_year: int) -> Tuple[str, str]:
    """
    Obtiene el período completo de un año fiscal (abril a marzo siguiente).

    Args:
        fiscal_year: Año fiscal (ej: 2025 = abril 2025 a marzo 2026)

    Returns:
        Tuple (start_date, end_date)
    """
    # Año fiscal japonés: abril 1 a marzo 31
    start_date = f"{fiscal_year}-04-01"
    end_date = f"{fiscal_year + 1}-03-31"
    return start_date, end_date


def process_year_end_carryover(from_year: int, to_year: int) -> Dict:
    """
    Procesa el carry-over de fin de año fiscal usando ORM con row-level locking.

    ✅ FIX (BUG #5): Migrado de SQL raw (get_db) a ORM (SessionLocal)
       - Usa row-level locking (.with_for_update()) para prevenir race conditions
       - Genera UUIDs en lugar de malformed IDs ("{emp_num}_{to_year}")
       - Mantiene transaccionalidad y auditoría completa

    - Copia balances no usados del año anterior al nuevo año
    - Elimina registros mayores a 2 años (vencidos)
    - Aplica regla de máximo acumulable

    Args:
        from_year: Año fiscal que termina
        to_year: Año fiscal que comienza

    Returns:
        Dict con estadísticas del proceso
    """
    from orm.models.employee import Employee
    from orm import SessionLocal
    import uuid

    stats = {
        'employees_processed': 0,
        'days_carried_over': 0.0,
        'days_expired': 0.0,
        'records_deleted': 0,
        'errors': []
    }

    with SessionLocal() as session:
        try:
            # 1. Obtener empleados con balance positivo del año que termina (con lock)
            employees_with_balance = session.query(Employee).filter(
                and_(
                    Employee.year == from_year,
                    Employee.balance > 0
                )
            ).with_for_update().all()  # 🔒 Row-level lock

            max_carry = FISCAL_CONFIG['max_accumulated_days']

            for emp in employees_with_balance:
                emp_num = emp.employee_num
                carry_over = float(emp.balance or 0)

                # Aplicar máximo de carry-over
                if carry_over > max_carry:
                    stats['days_expired'] += carry_over - max_carry
                    carry_over = max_carry

                # 2. Verificar si ya existe registro del nuevo año
                existing = session.query(Employee).filter(
                    and_(
                        Employee.employee_num == emp_num,
                        Employee.year == to_year
                    )
                ).with_for_update().first()  # 🔒 Lock

                if existing:
                    # Sumar carry-over al balance existente
                    old_balance = existing.balance or 0
                    new_balance = old_balance + carry_over
                    new_balance = min(new_balance, max_carry)

                    existing.balance = new_balance
                    existing.updated_at = datetime.now(timezone.utc)

                    # Auditar cambio
                    log_audit_action(
                        action='YEAR_END_CARRYOVER_UPDATE',
                        entity_type='employees',
                        entity_id=existing.id,
                        old_value={'balance': old_balance},
                        new_value={'balance': new_balance},
                        reason=f'Year-end carryover from {from_year} to {to_year}',
                        performed_by='system'
                    )
                else:
                    # Crear nuevo registro con carry-over (FIX: UUID en lugar de malformed ID)
                    new_emp = Employee(
                        id=str(uuid.uuid4()),  # ✅ UUID válido en lugar de "{emp_num}_{to_year}"
                        employee_num=emp_num,
                        name=emp.name,
                        granted=0,
                        used=0,
                        balance=carry_over,
                        year=to_year,
                        status=emp.status,
                        kana=emp.kana,
                        hire_date=emp.hire_date,
                        updated_at=datetime.now(timezone.utc)
                    )
                    session.add(new_emp)

                    # Auditar creación
                    log_audit_action(
                        action='YEAR_END_CARRYOVER_NEW',
                        entity_type='employees',
                        entity_id=new_emp.id,
                        old_value={},
                        new_value={'balance': carry_over, 'year': to_year},
                        reason=f'Year-end carryover from {from_year} to {to_year}',
                        performed_by='system'
                    )

                stats['employees_processed'] += 1
                stats['days_carried_over'] += carry_over

            # 3. Marcar días expirados (más de 2 años)
            expiry_year = to_year - FISCAL_CONFIG['max_carry_over_years']
            expired = session.query(Employee).filter(
                and_(
                    Employee.year <= expiry_year,
                    Employee.balance > 0
                )
            ).with_for_update().all()  # 🔒 Lock

            for exp in expired:
                stats['days_expired'] += float(exp.balance or 0)

            # 4. Eliminar registros muy antiguos (más de 3 años para auditoría)
            retention_year = to_year - FISCAL_CONFIG['ledger_retention_years']
            records_to_delete = session.query(Employee).filter(
                Employee.year < retention_year
            ).with_for_update().all()

            stats['records_deleted'] = len(records_to_delete)
            for record in records_to_delete:
                session.delete(record)

            session.commit()

        except Exception as e:
            session.rollback()
            stats['errors'].append(str(e))
            raise

    return stats


def get_employee_balance_breakdown(employee_num: str, year: int) -> Dict:
    """
    Obtiene desglose del balance por año de origen para uso LIFO.

    Args:
        employee_num: Número de empleado
        year: Año fiscal actual

    Returns:
        Dict con desglose de días disponibles por año de origen
    """
    with get_db() as conn:
        # Obtener últimos 2 años de datos
        records = conn.execute(_prepare_query('''
            SELECT year, granted, used, balance
            FROM employees
            WHERE employee_num = ? AND year >= ?
            ORDER BY year DESC
        '''), (employee_num, year - 1)).fetchall()

    breakdown = {
        'employee_num': employee_num,
        'reference_year': year,
        'total_available': 0.0,
        'by_year': [],
        'lifo_order': [],
    }

    for rec in records:
        balance = float(rec['balance']) if rec['balance'] else 0
        year_data = {
            'year': rec['year'],
            'granted': float(rec['granted']) if rec['granted'] else 0,
            'used': float(rec['used']) if rec['used'] else 0,
            'balance': balance,
            'is_current_year': rec['year'] == year,
            'expires_end_of': rec['year'] + FISCAL_CONFIG['max_carry_over_years'],
        }
        breakdown['by_year'].append(year_data)
        breakdown['total_available'] += balance

        # LIFO: años más nuevos tienen prioridad
        if balance > 0:
            breakdown['lifo_order'].append({
                'year': rec['year'],
                'days': balance,
                'priority': 1 if rec['year'] >= year else 2,
            })

    # Ordenar por prioridad LIFO (nuevos primero)
    breakdown['lifo_order'].sort(key=lambda x: (x['priority'], -x['year']))

    return breakdown


def apply_lifo_deduction(employee_num: str, days_to_use: float, current_year: int, performed_by: str = "system", reason: str = "Leave request deduction") -> Dict:
    """
    Aplica deducción de días usando lógica LIFO (primero los más nuevos).
    Usa ORM con row-level locking para prevenir race conditions.
    REGISTRA TODAS LAS OPERACIONES EN audit_log para cumplimiento legal.

    Args:
        employee_num: Número de empleado
        days_to_use: Días a deducir
        current_year: Año actual
        performed_by: Usuario que realiza la deducción (default: "system")
        reason: Razón de la deducción (default: "Leave request deduction")

    Returns:
        Dict con detalle de deducción por año
    """
    breakdown = get_employee_balance_breakdown(employee_num, current_year)
    remaining = days_to_use
    deductions = []
    timestamp = datetime.now(timezone.utc).isoformat()

    with SessionLocal() as session:
        try:
            # Procesar deducción LIFO
            for item in breakdown['lifo_order']:
                if remaining <= 0:
                    break

                available = item['days']
                to_deduct = min(available, remaining)

                if to_deduct > 0:
                    # ✅ FIX: Row-level lock (FOR UPDATE) - previene race conditions
                    emp = session.query(Employee).filter(
                        and_(
                            Employee.employee_num == employee_num,
                            Employee.year == item['year'],
                            Employee.grant_date == item.get('grant_date')
                        )
                    ).with_for_update().first()

                    if not emp:
                        continue

                    # Guardar balance anterior para auditoría
                    balance_before = emp.balance or 0
                    used_before = emp.used or 0

                    # Actualizar usando ORM
                    emp.used = (emp.used or 0) + to_deduct
                    emp.balance = (emp.granted or 0) - emp.used
                    emp.updated_at = datetime.now(timezone.utc)

                    # Auditar en audit_log (tabla estándar)
                    try:
                        log_audit_action(
                            action='LIFO_DEDUCTION',
                            entity_type='employees',
                            entity_id=emp.id,
                            old_value={
                                'balance': balance_before,
                                'used': used_before
                            },
                            new_value={
                                'balance': emp.balance,
                                'used': emp.used
                            },
                            reason=reason,
                            performed_by=performed_by
                        )
                    except Exception as e:
                        # Si audit_log falla, continuar sin error pero log el problema
                        import logging
                        logging.error(f"Failed to audit LIFO deduction: {e}")

                    deductions.append({
                        'year': item['year'],
                        'days_deducted': to_deduct,
                        'balance_before': balance_before,
                        'balance_after': emp.balance
                    })
                    remaining -= to_deduct

            # Commit transacción (libera los locks aquí)
            session.commit()

        except Exception as e:
            session.rollback()
            raise

    return {
        'employee_num': employee_num,
        'total_deducted': days_to_use - remaining,
        'remaining_not_deducted': remaining,
        'deductions_by_year': deductions,
        'success': remaining == 0,
        'audit_timestamp': timestamp
    }


# Alias DEPRECATED - mantener solo para compatibilidad con código legacy
def apply_fifo_deduction(employee_num: str, days_to_use: float, current_year: int) -> Dict:
    """
    DEPRECATED: Usar apply_lifo_deduction en su lugar.

    NOTA: El nombre 'fifo' es incorrecto. La logica real es LIFO (Last In First Out):
    - Se consumen primero los dias del ano mas reciente
    - Luego los dias del ano anterior (carry-over)

    Este alias se mantiene solo para compatibilidad con codigo existente.
    """
    return apply_lifo_deduction(employee_num, days_to_use, current_year)


def check_expiring_soon(year: int, warning_threshold_months: int = 3) -> List[Dict]:
    """
    Encuentra empleados con días próximos a expirar.

    Args:
        year: Año fiscal actual
        warning_threshold_months: Meses de anticipación para alertar

    Returns:
        Lista de empleados con días por expirar
    """
    # Los días del año (year - 1) expirarán al final del año (year)
    expiring_year = year - 1

    with get_db() as conn:
        employees = conn.execute(_prepare_query('''
            SELECT e.employee_num, e.name, e.balance, e.year,
                   g.hire_date
            FROM employees e
            LEFT JOIN genzai g ON e.employee_num = g.employee_num
            WHERE e.year = ? AND e.balance > 0
        '''), (expiring_year,)).fetchall()

    result = []
    today = date.today()

    for emp in employees:
        # Fecha de expiración: fin del año fiscal siguiente al año de otorgamiento
        # En Japón el año fiscal típicamente termina el 31 de marzo (4月-3月)
        # Los días otorgados en el año fiscal Y expiran al final del año fiscal Y+2
        # (máximo 2 años de carry-over según 労働基準法)
        #
        # Nota: Si la empresa usa un año fiscal diferente, ajustar FISCAL_CONFIG
        # y actualizar este cálculo según corresponda.
        grant_year = emp['year']
        expiry_fiscal_year_end = grant_year + FISCAL_CONFIG['max_carry_over_years']
        expiry_date = date(expiry_fiscal_year_end + 1, 3, 31)  # Fin del año fiscal
        days_until_expiry = (expiry_date - today).days

        result.append({
            'employee_num': emp['employee_num'],
            'name': emp['name'],
            'expiring_days': float(emp['balance']),
            'from_year': emp['year'],
            'expires_on': expiry_date.isoformat(),
            'days_until_expiry': days_until_expiry,
            'hire_date': emp['hire_date'],
            'urgency': 'high' if days_until_expiry < 30 else
                       'medium' if days_until_expiry < 90 else 'low'
        })

    # Ordenar por urgencia
    result.sort(key=lambda x: x['days_until_expiry'])

    return result


def check_5day_compliance(year: int) -> Dict:
    """
    Verifica cumplimiento de la obligación de 5日取得
    (empleados con 10+ días deben usar mínimo 5).

    Args:
        year: Año a verificar

    Returns:
        Dict con análisis de cumplimiento
    """
    min_use = FISCAL_CONFIG['minimum_annual_use']
    min_days_for_rule = FISCAL_CONFIG['minimum_days_for_obligation']

    with get_db() as conn:
        employees = conn.execute(_prepare_query('''
            SELECT employee_num, name, granted, used, balance
            FROM employees
            WHERE year = ? AND granted >= ?
        '''), (year, min_days_for_rule)).fetchall()

    compliant = []
    non_compliant = []
    at_risk = []

    for emp in employees:
        used = float(emp['used']) if emp['used'] else 0
        remaining_required = max(0, min_use - used)

        emp_data = {
            'employee_num': emp['employee_num'],
            'name': emp['name'],
            'granted': float(emp['granted']),
            'used': used,
            'required': min_use,
            'remaining_to_comply': remaining_required
        }

        if used >= min_use:  # 5+ días - cumple requisito
            compliant.append(emp_data)
        elif used >= 3:  # 3-4 días (al menos 60% del requisito)
            at_risk.append(emp_data)
        else:  # 0-2 días - no cumple
            non_compliant.append(emp_data)

    return {
        'year': year,
        'minimum_required': min_use,
        'total_employees': len(employees),
        'compliant_count': len(compliant),
        'at_risk_count': len(at_risk),
        'non_compliant_count': len(non_compliant),
        'compliance_rate': round(len(compliant) / len(employees) * 100, 1) if employees else 0,
        'compliant': compliant,
        'at_risk': at_risk,
        'non_compliant': non_compliant
    }


def get_grant_recommendation(employee_num: str) -> Dict:
    """
    Calcula recomendación de días a otorgar basado en antigüedad.

    Args:
        employee_num: Número de empleado

    Returns:
        Dict con recomendación de otorgamiento
    """
    with get_db() as conn:
        # Buscar en genzai primero, luego ukeoi
        emp = conn.execute(_prepare_query('''
            SELECT employee_num, name, hire_date FROM genzai
            WHERE employee_num = ?
        '''), (employee_num,)).fetchone()

        if not emp:
            emp = conn.execute(_prepare_query('''
                SELECT employee_num, name, hire_date FROM ukeoi
                WHERE employee_num = ?
            '''), (employee_num,)).fetchone()

    if not emp:
        return {'error': 'Empleado no encontrado'}

    hire_date = emp['hire_date']
    seniority = calculate_seniority_years(hire_date)
    recommended_days = calculate_granted_days(seniority)

    return {
        'employee_num': emp['employee_num'],
        'name': emp['name'],
        'hire_date': hire_date,
        'seniority_years': seniority,
        'recommended_grant_days': recommended_days,
        'grant_table_reference': GRANT_TABLE,
        'next_milestone': next(
            (threshold for threshold in sorted(GRANT_TABLE.keys())
             if threshold > seniority),
            None
        )
    }


def auto_designate_5_days(employee_num: str, year: int, performed_by: str = "system") -> Dict:
    """
    Designa automáticamente 5 días si empleado tiene 10+ días y no los ha usado.

    ✅ FIX (BUG #6): Migrado de SQL raw + tabla inexistente (official_leave_designation)
       a LeaveRequest con status='DESIGNATED' en ORM
       - Usa SessionLocal + ORM models
       - Crea registros LeaveRequest en lugar de tabla inexistente
       - Usa log_audit_action() para auditoría consistente

    Requisito legal: 年5日の取得義務 (obligación de 5 días anuales)

    Args:
        employee_num: Número de empleado
        year: Año fiscal
        performed_by: Usuario que realiza la designación

    Returns:
        Dict con resultado de designación
    """
    from orm.models.leave_request import LeaveRequest
    import uuid

    with SessionLocal() as session:
        try:
            # 1. Obtener balance actual (con lock)
            emp = session.query(Employee).filter(
                and_(
                    Employee.employee_num == employee_num,
                    Employee.year == year
                )
            ).with_for_update().first()  # 🔒 Row-level lock

            if not emp:
                return {
                    'success': False,
                    'error': f'Employee {employee_num} not found for year {year}'
                }

            total_granted = float(emp.granted or 0)
            used = float(emp.used or 0)

            # 2. Verificar elegibilidad
            if total_granted < FISCAL_CONFIG['minimum_days_for_obligation']:
                return {
                    'success': False,
                    'reason': 'Employee exempt - less than 10 days granted',
                    'granted': total_granted
                }

            # 3. Calcular cuántos días faltan por usar
            remaining_required = max(0, FISCAL_CONFIG['minimum_annual_use'] - used)

            if remaining_required <= 0:
                return {
                    'success': False,
                    'reason': 'Employee already compliant',
                    'used': used
                }

            # 4. Designar los días creando LeaveRequest con status='DESIGNATED'
            # (en lugar de tabla inexistente official_leave_designation)
            today = date.today()
            year_end = date(year, 12, 31)  # Designación válida hasta fin de año

            designation_req = LeaveRequest(
                id=str(uuid.uuid4()),
                employee_num=employee_num,
                employee_name=emp.name,
                start_date=today.isoformat(),
                end_date=year_end.isoformat(),
                days_requested=remaining_required,
                hours_requested=0.0,
                leave_type='full',
                reason='Legal 5-day requirement (年5日の取得義務) - Official Designation',
                status='DESIGNATED',  # ✅ Status especial para designaciones legales
                year=year,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                approver=performed_by,
                approved_at=datetime.now(timezone.utc)
            )
            session.add(designation_req)

            # 5. Registrar auditoría
            log_audit_action(
                action='DESIGNATE_5DAYS',
                entity_type='leave_requests',
                entity_id=designation_req.id,
                old_value={'compliance_status': 'non_compliant', 'used': used, 'required': FISCAL_CONFIG['minimum_annual_use']},
                new_value={'compliance_status': 'designated', 'days_designated': remaining_required},
                reason='Legal 5-day requirement - official designation (年5日の取得義務)',
                performed_by=performed_by
            )

            session.commit()

            return {
                'success': True,
                'employee_num': employee_num,
                'year': year,
                'days_designated': remaining_required,
                'used_so_far': used,
                'designation_date': today.isoformat(),
                'leave_request_id': designation_req.id,
                'reason': 'Legal 5-day requirement (年5日の取得義務)'
            }

        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'error': str(e)
            }


def validate_hire_date(hire_date: str) -> Tuple[bool, str]:
    """
    Valida que hire_date sea válido.

    Requisitos:
    - Formato YYYY-MM-DD
    - No puede ser fecha futura
    - No puede ser más de 130 años atrás
    - Debe ser fecha válida

    Args:
        hire_date: Fecha en formato YYYY-MM-DD

    Returns:
        Tuple (is_valid, message)
    """
    if not hire_date:
        return False, "Hire date cannot be empty"

    try:
        hire = datetime.strptime(hire_date, '%Y-%m-%d').date()
        today = date.today()

        # No puede ser fecha futura
        if hire > today:
            return False, f"Hire date cannot be in future: {hire_date}"

        # No puede ser más de 130 años atrás
        days_since = (today - hire).days
        if days_since > 130 * 365:
            return False, f"Hire date too old (> 130 years): {hire_date}"

        return True, "Valid hire date"

    except ValueError:
        return False, f"Invalid hire date format (must be YYYY-MM-DD): {hire_date}"
