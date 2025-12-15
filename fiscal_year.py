"""
Módulo de gestión del año fiscal de vacaciones (有給休暇)

Características:
- Período de cierre: 21日〜20日 (configurable)
- Carry-over máximo: 2 años
- Uso FIFO: días más antiguos primero
- Tabla de otorgamiento según antigüedad (Ley Laboral Japonesa)
"""

from datetime import date, datetime
from typing import Optional, Dict, List, Tuple
import sqlite3
from contextlib import contextmanager

DB_NAME = "yukyu.db"

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


@contextmanager
def get_db():
    """Context manager para conexiones seguras a BD"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


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
    Procesa el carry-over de fin de año fiscal.

    - Copia balances no usados del año anterior al nuevo año
    - Elimina registros mayores a 2 años (vencidos)
    - Aplica regla de máximo acumulable

    Args:
        from_year: Año fiscal que termina
        to_year: Año fiscal que comienza

    Returns:
        Dict con estadísticas del proceso
    """
    stats = {
        'employees_processed': 0,
        'days_carried_over': 0.0,
        'days_expired': 0.0,
        'records_deleted': 0,
        'errors': []
    }

    with get_db() as conn:
        try:
            conn.execute("BEGIN TRANSACTION")
            c = conn.cursor()

            # 1. Obtener empleados con balance positivo del año que termina
            employees_with_balance = c.execute('''
                SELECT employee_num, name, balance, granted, used, year
                FROM employees
                WHERE year = ? AND balance > 0
            ''', (from_year,)).fetchall()

            for emp in employees_with_balance:
                emp_num = emp['employee_num']
                carry_over = float(emp['balance'])

                # Aplicar máximo de carry-over
                max_carry = FISCAL_CONFIG['max_accumulated_days']
                if carry_over > max_carry:
                    stats['days_expired'] += carry_over - max_carry
                    carry_over = max_carry

                # 2. Verificar si ya existe registro del nuevo año
                existing = c.execute('''
                    SELECT id, granted, used, balance FROM employees
                    WHERE employee_num = ? AND year = ?
                ''', (emp_num, to_year)).fetchone()

                if existing:
                    # Sumar carry-over al balance existente
                    new_balance = float(existing['balance']) + carry_over
                    new_balance = min(new_balance, max_carry)

                    c.execute('''
                        UPDATE employees
                        SET balance = ?, last_updated = ?
                        WHERE id = ?
                    ''', (new_balance, datetime.now().isoformat(), existing['id']))
                else:
                    # Crear nuevo registro con carry-over
                    new_id = f"{emp_num}_{to_year}"
                    c.execute('''
                        INSERT INTO employees
                        (id, employee_num, name, granted, used, balance, year, last_updated)
                        VALUES (?, ?, ?, 0, 0, ?, ?, ?)
                    ''', (new_id, emp_num, emp['name'], carry_over, to_year,
                          datetime.now().isoformat()))

                stats['employees_processed'] += 1
                stats['days_carried_over'] += carry_over

            # 3. Marcar/eliminar días expirados (más de 2 años)
            expiry_year = to_year - FISCAL_CONFIG['max_carry_over_years']
            expired = c.execute('''
                SELECT employee_num, balance FROM employees
                WHERE year <= ? AND balance > 0
            ''', (expiry_year,)).fetchall()

            for exp in expired:
                stats['days_expired'] += float(exp['balance'])

            # 4. Eliminar registros muy antiguos (más de 3 años para auditoría)
            retention_year = to_year - FISCAL_CONFIG['ledger_retention_years']
            c.execute('DELETE FROM employees WHERE year < ?', (retention_year,))
            stats['records_deleted'] = c.rowcount

            conn.commit()

        except Exception as e:
            conn.rollback()
            stats['errors'].append(str(e))
            raise

    return stats


def get_employee_balance_breakdown(employee_num: str, year: int) -> Dict:
    """
    Obtiene desglose del balance por año de origen para uso FIFO.

    Args:
        employee_num: Número de empleado
        year: Año fiscal actual

    Returns:
        Dict con desglose de días disponibles por año de origen
    """
    with get_db() as conn:
        # Obtener últimos 2 años de datos
        records = conn.execute('''
            SELECT year, granted, used, balance
            FROM employees
            WHERE employee_num = ? AND year >= ?
            ORDER BY year ASC
        ''', (employee_num, year - 1)).fetchall()

    breakdown = {
        'employee_num': employee_num,
        'reference_year': year,
        'total_available': 0.0,
        'by_year': [],
        'fifo_order': [],
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

        # FIFO: años más antiguos tienen prioridad
        if balance > 0:
            breakdown['fifo_order'].append({
                'year': rec['year'],
                'days': balance,
                'priority': 1 if rec['year'] < year else 2,
            })

    # Ordenar por prioridad FIFO (antiguos primero)
    breakdown['fifo_order'].sort(key=lambda x: (x['priority'], x['year']))

    return breakdown


def apply_fifo_deduction(employee_num: str, days_to_use: float, current_year: int) -> Dict:
    """
    Aplica deducción de días usando lógica FIFO (primero los más antiguos).

    Args:
        employee_num: Número de empleado
        days_to_use: Días a deducir
        current_year: Año actual

    Returns:
        Dict con detalle de deducción por año
    """
    breakdown = get_employee_balance_breakdown(employee_num, current_year)
    remaining = days_to_use
    deductions = []

    with get_db() as conn:
        try:
            conn.execute("BEGIN TRANSACTION")
            c = conn.cursor()

            for item in breakdown['fifo_order']:
                if remaining <= 0:
                    break

                available = item['days']
                to_deduct = min(available, remaining)

                if to_deduct > 0:
                    # Actualizar balance de ese año
                    c.execute('''
                        UPDATE employees
                        SET used = used + ?,
                            balance = balance - ?,
                            last_updated = ?
                        WHERE employee_num = ? AND year = ?
                    ''', (to_deduct, to_deduct, datetime.now().isoformat(),
                          employee_num, item['year']))

                    deductions.append({
                        'year': item['year'],
                        'days_deducted': to_deduct
                    })
                    remaining -= to_deduct

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise

    return {
        'employee_num': employee_num,
        'total_deducted': days_to_use - remaining,
        'remaining_not_deducted': remaining,
        'deductions_by_year': deductions,
        'success': remaining == 0
    }


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
        employees = conn.execute('''
            SELECT e.employee_num, e.name, e.balance, e.year,
                   g.hire_date
            FROM employees e
            LEFT JOIN genzai g ON e.employee_num = g.employee_num
            WHERE e.year = ? AND e.balance > 0
        ''', (expiring_year,)).fetchall()

    result = []
    today = date.today()

    for emp in employees:
        # Fecha de expiración: fin del año fiscal actual (31 marzo)
        expiry_date = date(year + 1, 3, 31)
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
        employees = conn.execute('''
            SELECT employee_num, name, granted, used, balance
            FROM employees
            WHERE year = ? AND granted >= ?
        ''', (year, min_days_for_rule)).fetchall()

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

        if used >= min_use:
            compliant.append(emp_data)
        elif remaining_required > 0 and remaining_required < min_use:
            at_risk.append(emp_data)
        else:
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
        emp = conn.execute('''
            SELECT employee_num, name, hire_date FROM genzai
            WHERE employee_num = ?
        ''', (employee_num,)).fetchone()

        if not emp:
            emp = conn.execute('''
                SELECT employee_num, name, hire_date FROM ukeoi
                WHERE employee_num = ?
            ''', (employee_num,)).fetchone()

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
