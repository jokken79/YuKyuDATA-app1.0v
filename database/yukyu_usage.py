import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator, Dict, List, Any
from services.crypto_utils import encrypt_field, decrypt_field, get_encryption_manager

# Import database connection manager
try:
    from database.connection import ConnectionManager
    USE_POSTGRESQL = os.getenv('DATABASE_TYPE', 'sqlite').lower() == 'postgresql'
except ImportError:
    # Fallback for SQLite if connection manager not available
    import sqlite3
    USE_POSTGRESQL = False

# Vercel compatibility: Use /tmp for serverless or custom path via env var
def get_db_path():
    """Get database path, handling Vercel serverless environment."""
    custom_path = os.getenv('DATABASE_PATH')
    if custom_path:
        return custom_path

    # Check if running on Vercel (serverless)
    if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        # Use /tmp for serverless (ephemeral storage)
        return '/tmp/yukyu.db'

    # Default: local directory
    return 'yukyu.db'

DB_NAME = get_db_path()
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DB_NAME}')

# Initialize connection manager for PostgreSQL
if USE_POSTGRESQL:
    db_manager = ConnectionManager(DATABASE_URL)
else:
    db_manager = None

def _get_param_placeholder() -> str:
    """Get parameter placeholder for current database."""
    return '%s' if USE_POSTGRESQL else '?'

def _convert_query_placeholders(query: str) -> str:
    """Convert SQLite ? placeholders to PostgreSQL %s if needed."""
    if not USE_POSTGRESQL:
        return query
    # Simple conversion - be careful with strings containing ?
    return query.replace('?', '%s')

def get_db_connection():
    """Get database connection (SQLite or PostgreSQL)."""
    if USE_POSTGRESQL:
        return db_manager.get_connection()
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


@contextmanager
def get_db() -> Generator:
    """Context manager for database connections to prevent memory leaks."""
    if USE_POSTGRESQL:
        # PostgreSQL connection from pool
        with db_manager.get_connection() as conn:
            yield conn
    else:
        # SQLite direct connection
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def init_db():
"""
Yukyu (paid leave) usage details and calculations.
Handles: Usage tracking, monthly summaries, recalculations
"""

        return True

def get_employee_yukyu_history(employee_num, current_year=None):
    """
    Gets employee's yukyu history for current year and previous year.
    Follows Japanese law: only keep last 2 years (3rd year gets deleted).
    """
    if not current_year:
        current_year = datetime.now().year

    with get_db() as conn:
        c = conn.cursor()

        # Get last 2 years of data
        years_to_fetch = [current_year, current_year - 1]

        rows = c.execute('''
            SELECT * FROM employees
            WHERE employee_num = ? AND year IN (?, ?)
            ORDER BY year DESC
        ''', (employee_num, years_to_fetch[0], years_to_fetch[1])).fetchall()

        return [dict(row) for row in rows]

def delete_old_yukyu_records(cutoff_year):
    """
    Deletes yukyu records older than cutoff year.
    Called to enforce 3-year carry-over rule (delete records from 3+ years ago).
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute("DELETE FROM employees WHERE year < ?", (cutoff_year,))
        deleted_count = c.rowcount

        conn.commit()
        return deleted_count

# === YUKYU USAGE DETAILS FUNCTIONS (Individual usage dates - v2.0 feature) ===

def save_yukyu_usage_details(usage_details_list):
    """
    Saves individual yukyu usage dates (columns R-BE from Excel).
    Each entry represents one specific date when an employee used yukyu.
    Works with SQLite and PostgreSQL.

    Args:
        usage_details_list: List of dicts with keys:
            - employee_num: Employee number
            - name: Employee name
            - use_date: Date of usage (YYYY-MM-DD format)
            - year: Year extracted from use_date
            - month: Month extracted from use_date
            - days_used: Number of days (default 1.0)
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for detail in usage_details_list:
            params = (
                detail.get('employee_num'),
                detail.get('name'),
                detail.get('use_date'),
                detail.get('year'),
                detail.get('month'),
                detail.get('days_used', 1.0),
                timestamp
            )

            if USE_POSTGRESQL:
                c.execute('''
                    INSERT INTO yukyu_usage_details
                    (employee_num, name, use_date, year, month, days_used, last_updated, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (employee_num, use_date) DO UPDATE SET
                        name = EXCLUDED.name,
                        year = EXCLUDED.year,
                        month = EXCLUDED.month,
                        days_used = EXCLUDED.days_used,
                        last_updated = EXCLUDED.last_updated
                ''', params + (timestamp,))
            else:
                c.execute('''
                    INSERT OR REPLACE INTO yukyu_usage_details
                    (employee_num, name, use_date, year, month, days_used, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', params)

        conn.commit()

def get_yukyu_usage_details(employee_num=None, year=None, month=None):
    """
    Gets individual yukyu usage dates.

    Args:
        employee_num: Filter by employee number (optional)
        year: Filter by year (optional)
        month: Filter by month (optional)

    Returns:
        List of usage detail records
    """
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM yukyu_usage_details WHERE 1=1"
        params = []

        if employee_num:
            query += " AND employee_num = ?"
            params.append(employee_num)

        if year:
            query += " AND year = ?"
            params.append(year)

        if month:
            query += " AND month = ?"
            params.append(month)

        query += " ORDER BY use_date DESC"

        rows = c.execute(query, tuple(params)).fetchall()
        return [dict(row) for row in rows]

def get_monthly_usage_summary(year):
    """
    Gets monthly usage summary for a specific year.
    Returns count of employees and total days used per month.

    Args:
        year: Year to summarize

    Returns:
        Dict with keys 1-12 (months) containing {employee_count, total_days}
    """
    with get_db() as conn:
        c = conn.cursor()

        rows = c.execute('''
            SELECT
                month,
                COUNT(DISTINCT employee_num) as employee_count,
                SUM(days_used) as total_days,
                COUNT(*) as usage_count
            FROM yukyu_usage_details
            WHERE year = ?
            GROUP BY month
            ORDER BY month
        ''', (year,)).fetchall()

        # Convert to dict for easy access
        result = {}
        for row in rows:
            result[row['month']] = {
                'employee_count': row['employee_count'],
                'total_days': row['total_days'],
                'usage_count': row['usage_count']
            }

        return result

def clear_yukyu_usage_details():
    """Clears all yukyu usage details from the database."""
    with get_db() as conn:
        conn.execute("DELETE FROM yukyu_usage_details")
        conn.commit()


# ============================================
# EDIT YUKYU USAGE DETAILS (NEW - v2.1 feature)
# Permite editar datos importados desde Excel
# ============================================

def update_yukyu_usage_detail(detail_id: int, days_used: float = None, use_date: str = None):
    """
    Actualiza un registro específico de uso de yukyu.
    Útil para corregir errores de importación (ej: medio día vs día completo).

    Args:
        detail_id: ID del registro a actualizar
        days_used: Nuevo valor de días usados (0.5, 1.0, etc)
        use_date: Nueva fecha (YYYY-MM-DD) - opcional

    Returns:
        dict con el registro actualizado
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Verificar que existe el registro
        existing = c.execute("SELECT * FROM yukyu_usage_details WHERE id = ?", (detail_id,)).fetchone()
        if not existing:
            raise ValueError(f"Registro ID {detail_id} no encontrado")

        # Construir query de actualización
        updates = []
        params = []

        if days_used is not None:
            updates.append("days_used = ?")
            params.append(days_used)

        if use_date is not None:
            updates.append("use_date = ?")
            params.append(use_date)
            # Actualizar año y mes también
            from datetime import datetime as dt
            parsed = dt.strptime(use_date, '%Y-%m-%d')
            updates.append("year = ?")
            params.append(parsed.year)
            updates.append("month = ?")
            params.append(parsed.month)

        if not updates:
            raise ValueError("Debes proporcionar al menos un campo para actualizar")

        updates.append("last_updated = ?")
        params.append(timestamp)
        params.append(detail_id)

        query = f"UPDATE yukyu_usage_details SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, tuple(params))
        conn.commit()

        # Retornar registro actualizado
        updated = c.execute("SELECT * FROM yukyu_usage_details WHERE id = ?", (detail_id,)).fetchone()
        return dict(updated)


def delete_yukyu_usage_detail(detail_id: int):
    """
    Elimina un registro específico de uso de yukyu.
    Útil para eliminar fechas importadas incorrectamente.

    Args:
        detail_id: ID del registro a eliminar

    Returns:
        dict con info del registro eliminado
    """
    with get_db() as conn:
        c = conn.cursor()

        # Obtener datos antes de eliminar
        existing = c.execute("SELECT * FROM yukyu_usage_details WHERE id = ?", (detail_id,)).fetchone()
        if not existing:
            raise ValueError(f"Registro ID {detail_id} no encontrado")

        result = dict(existing)

        # Eliminar
        c.execute("DELETE FROM yukyu_usage_details WHERE id = ?", (detail_id,))
        conn.commit()

        return result


def add_single_yukyu_usage(employee_num: str, name: str, use_date: str, days_used: float = 1.0):
    """
    Agrega un nuevo registro individual de uso de yukyu.
    Útil para agregar fechas que no se importaron correctamente del Excel.

    Args:
        employee_num: Número de empleado
        name: Nombre del empleado
        use_date: Fecha de uso (YYYY-MM-DD)
        days_used: Días usados (0.5, 1.0, etc) - default 1.0

    Returns:
        dict con el nuevo registro creado
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Parsear fecha para obtener año y mes
        from datetime import datetime as dt
        parsed = dt.strptime(use_date, '%Y-%m-%d')
        year = parsed.year
        month = parsed.month

        # Verificar si ya existe
        existing = c.execute(
            "SELECT id FROM yukyu_usage_details WHERE employee_num = ? AND use_date = ?",
            (employee_num, use_date)
        ).fetchone()

        if existing:
            raise ValueError(f"Ya existe un registro para empleado {employee_num} en fecha {use_date}")

        # Insertar nuevo registro
        c.execute('''
            INSERT INTO yukyu_usage_details
            (employee_num, name, use_date, year, month, days_used, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (employee_num, name, use_date, year, month, days_used, timestamp))

        new_id = c.lastrowid
        conn.commit()

        # Retornar registro creado
        created = c.execute("SELECT * FROM yukyu_usage_details WHERE id = ?", (new_id,)).fetchone()
        return dict(created)


def recalculate_employee_used_days(employee_num: str, year: int):
    """
    Recalcula los días usados de un empleado basándose en yukyu_usage_details.
    Actualiza la tabla employees automáticamente.

    Args:
        employee_num: Número de empleado
        year: Año fiscal

    Returns:
        dict con el resultado del recálculo
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Calcular total de días usados desde los detalles
        result = c.execute('''
            SELECT COALESCE(SUM(days_used), 0) as total_used
            FROM yukyu_usage_details
            WHERE employee_num = ? AND year = ?
        ''', (employee_num, year)).fetchone()

        new_used = result['total_used'] if result else 0.0

        # Obtener datos actuales del empleado
        employee_id = f"{employee_num}_{year}"
        employee = c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()

        if not employee:
            return {
                "employee_num": employee_num,
                "year": year,
                "error": f"Empleado {employee_id} no encontrado en tabla employees",
                "calculated_used": new_used
            }

        old_used = employee['used'] or 0.0
        granted = employee['granted'] or 0.0
        new_balance = granted - new_used
        new_usage_rate = (new_used / granted * 100) if granted > 0 else 0.0

        # Actualizar empleado
        c.execute('''
            UPDATE employees
            SET used = ?, balance = ?, usage_rate = ?, last_updated = ?
            WHERE id = ?
        ''', (new_used, new_balance, new_usage_rate, timestamp, employee_id))

        conn.commit()

        return {
            "employee_num": employee_num,
            "year": year,
            "old_used": old_used,
            "new_used": new_used,
            "granted": granted,
            "new_balance": new_balance,
            "new_usage_rate": round(new_usage_rate, 2)
        }


def update_employee(employee_num: str, year: int, **kwargs):
    """
    Actualiza campos específicos de un empleado.
    Útil para corregir datos importados incorrectamente.

    Args:
        employee_num: Número de empleado
        year: Año fiscal
        **kwargs: Campos a actualizar (granted, used, balance, haken, name, etc)

    Returns:
        dict con el empleado actualizado
    """
    allowed_fields = {'name', 'haken', 'granted', 'used', 'balance', 'expired', 'usage_rate'}

    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        employee_id = f"{employee_num}_{year}"

        # Verificar que existe
        existing = c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if not existing:
            raise ValueError(f"Empleado {employee_id} no encontrado")

        # Filtrar solo campos permitidos
        updates = []
        params = []

        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                params.append(value)

        if not updates:
            raise ValueError(f"No se proporcionaron campos válidos. Campos permitidos: {allowed_fields}")

        # Si se actualizó granted o used, recalcular balance y usage_rate
        new_granted = kwargs.get('granted', existing['granted'])
        new_used = kwargs.get('used', existing['used'])

        if 'granted' in kwargs or 'used' in kwargs:
            new_balance = new_granted - new_used
            new_usage_rate = (new_used / new_granted * 100) if new_granted > 0 else 0.0

            if 'balance' not in kwargs:
                updates.append("balance = ?")
                params.append(new_balance)
            if 'usage_rate' not in kwargs:
                updates.append("usage_rate = ?")
                params.append(new_usage_rate)

        updates.append("last_updated = ?")
        params.append(timestamp)
        params.append(employee_id)

        query = f"UPDATE employees SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, tuple(params))
        conn.commit()

        # Retornar registro actualizado
        updated = c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        return dict(updated)


def get_employee_usage_summary(employee_num: str, year: int):
    """
    Obtiene un resumen completo del uso de yukyu de un empleado.
    Incluye datos agregados y detalles individuales.

    Args:
        employee_num: Número de empleado
        year: Año fiscal

    Returns:
        dict con resumen completo
    """
    with get_db() as conn:
        c = conn.cursor()

        employee_id = f"{employee_num}_{year}"

        # Datos del empleado
        employee = c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()

        # Detalles de uso
        details = c.execute('''
            SELECT * FROM yukyu_usage_details
            WHERE employee_num = ? AND year = ?
            ORDER BY use_date ASC
        ''', (employee_num, year)).fetchall()

        # Calcular totales desde detalles
        total_from_details = sum(d['days_used'] for d in details) if details else 0

        return {
            "employee": dict(employee) if employee else None,
            "usage_details": [dict(d) for d in details],
            "summary": {
                "total_records": len(details),
                "total_days_from_details": total_from_details,
                "employee_used": employee['used'] if employee else None,
                "discrepancy": (employee['used'] - total_from_details) if employee else None
            }
        }


# ============================================
# CANCEL/REVERT LEAVE REQUESTS
# ============================================

def cancel_leave_request(request_id):
    """
    Cancela una solicitud PENDIENTE.
    Solo funciona si el status es 'PENDING'.

    Args:
        request_id: ID de la solicitud

    Returns:
        dict con info de la solicitud cancelada
    """
    with get_db() as conn:
        c = conn.cursor()

        # Get request details
        request = c.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()

        if not request:
            raise ValueError(f"Solicitud {request_id} no encontrada")

        if request['status'] != 'PENDING':
            raise ValueError(f"Solo se pueden cancelar solicitudes pendientes. Estado actual: {request['status']}")

        # Delete the request
        c.execute("DELETE FROM leave_requests WHERE id = ?", (request_id,))

        conn.commit()

        return {
            "request_id": request_id,
            "employee_num": request['employee_num'],
            "employee_name": request['employee_name'],
            "days_requested": request['days_requested']
        }

