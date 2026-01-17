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
Bulk operations for batch processing multiple employees.
Handles: Bulk updates, history, and reversions
"""

# ============================================

def init_bulk_audit_table():
    """Creates the bulk_update_audit table for tracking mass changes."""
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS bulk_update_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT NOT NULL,
                employee_num TEXT NOT NULL,
                year INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                updated_by TEXT DEFAULT 'system',
                updated_at TEXT NOT NULL,
                batch_size INTEGER DEFAULT 1,
                UNIQUE(operation_id, employee_num, field_name)
            )
        ''')

        c.execute('CREATE INDEX IF NOT EXISTS idx_bulk_audit_operation ON bulk_update_audit(operation_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bulk_audit_employee ON bulk_update_audit(employee_num)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bulk_audit_date ON bulk_update_audit(updated_at)')

        conn.commit()


def bulk_update_employees(employee_nums: List[str], year: int, updates: Dict[str, Any],
                          updated_by: str = "system") -> Dict[str, Any]:
    """
    Actualiza multiples empleados en una sola operacion.
    Implementa validaciones y audit trail.

    Args:
        employee_nums: Lista de numeros de empleado a actualizar
        year: Año fiscal
        updates: Diccionario con campos a actualizar:
            - add_granted: float (dias a sumar a granted)
            - add_used: float (dias a sumar a used)
            - set_haken: str (nuevo valor de haken/factory)
            - set_granted: float (establecer dias otorgados)
            - set_used: float (establecer dias usados)
        updated_by: Usuario que realiza la operacion

    Returns:
        Dict con resultados de la operacion:
            - success: bool
            - updated_count: int
            - errors: list
            - operation_id: str
            - audit_records: list
            - warnings: list (e.g., balance negativo)
    """
    import uuid

    # Validate max 50 employees per operation
    if len(employee_nums) > 50:
        raise ValueError("Maximo 50 empleados por operacion de bulk update")

    if not updates:
        raise ValueError("Se debe proporcionar al menos un campo para actualizar")

    # Valid update fields
    valid_fields = {'add_granted', 'add_used', 'set_haken', 'set_granted', 'set_used'}
    invalid_fields = set(updates.keys()) - valid_fields
    if invalid_fields:
        raise ValueError(f"Campos invalidos: {invalid_fields}. Campos validos: {valid_fields}")

    # Initialize audit table if not exists
    init_bulk_audit_table()

    operation_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()

    results = {
        "success": True,
        "updated_count": 0,
        "errors": [],
        "warnings": [],
        "operation_id": operation_id,
        "audit_records": [],
        "details": []
    }

    with get_db() as conn:
        c = conn.cursor()

        for emp_num in employee_nums:
            employee_id = f"{emp_num}_{year}"

            try:
                # Get current employee data
                employee = c.execute(
                    "SELECT * FROM employees WHERE id = ?",
                    (employee_id,)
                ).fetchone()

                if not employee:
                    results["errors"].append({
                        "employee_num": emp_num,
                        "error": f"Empleado {employee_id} no encontrado"
                    })
                    continue

                emp_data = dict(employee)
                old_values = {}
                new_values = {}
                update_parts = []
                params = []

                # Process add_granted (sumar a dias otorgados)
                if 'add_granted' in updates and updates['add_granted']:
                    add_amount = float(updates['add_granted'])
                    old_granted = emp_data.get('granted', 0) or 0
                    new_granted = old_granted + add_amount

                    if new_granted > 40:
                        results["warnings"].append({
                            "employee_num": emp_num,
                            "warning": f"Granted excede 40 dias ({new_granted:.1f})"
                        })

                    old_values['granted'] = old_granted
                    new_values['granted'] = new_granted
                    update_parts.append("granted = ?")
                    params.append(new_granted)

                # Process set_granted (establecer dias otorgados)
                if 'set_granted' in updates and updates['set_granted'] is not None:
                    new_granted = float(updates['set_granted'])
                    old_granted = emp_data.get('granted', 0) or 0

                    if new_granted > 40:
                        results["warnings"].append({
                            "employee_num": emp_num,
                            "warning": f"Granted excede 40 dias ({new_granted:.1f})"
                        })

                    old_values['granted'] = old_granted
                    new_values['granted'] = new_granted
                    update_parts.append("granted = ?")
                    params.append(new_granted)

                # Process add_used (sumar a dias usados)
                if 'add_used' in updates and updates['add_used']:
                    add_amount = float(updates['add_used'])
                    old_used = emp_data.get('used', 0) or 0
                    new_used = old_used + add_amount

                    old_values['used'] = old_used
                    new_values['used'] = new_used
                    update_parts.append("used = ?")
                    params.append(new_used)

                # Process set_used (establecer dias usados)
                if 'set_used' in updates and updates['set_used'] is not None:
                    new_used = float(updates['set_used'])
                    old_used = emp_data.get('used', 0) or 0

                    old_values['used'] = old_used
                    new_values['used'] = new_used
                    update_parts.append("used = ?")
                    params.append(new_used)

                # Process set_haken (cambiar派遣先)
                if 'set_haken' in updates and updates['set_haken']:
                    old_haken = emp_data.get('haken', '')
                    new_haken = str(updates['set_haken'])

                    old_values['haken'] = old_haken
                    new_values['haken'] = new_haken
                    update_parts.append("haken = ?")
                    params.append(new_haken)

                if not update_parts:
                    continue

                # Recalculate balance and usage_rate if granted or used changed
                final_granted = new_values.get('granted', emp_data.get('granted', 0) or 0)
                final_used = new_values.get('used', emp_data.get('used', 0) or 0)

                if 'granted' in new_values or 'used' in new_values:
                    new_balance = final_granted - final_used
                    new_usage_rate = (final_used / final_granted * 100) if final_granted > 0 else 0

                    # Check for negative balance warning
                    if new_balance < 0:
                        results["warnings"].append({
                            "employee_num": emp_num,
                            "name": emp_data.get('name', 'Unknown'),
                            "warning": f"Balance negativo: {new_balance:.1f} dias",
                            "balance": new_balance
                        })

                    update_parts.append("balance = ?")
                    params.append(new_balance)
                    update_parts.append("usage_rate = ?")
                    params.append(round(new_usage_rate, 2))

                    old_values['balance'] = emp_data.get('balance', 0)
                    new_values['balance'] = new_balance
                    old_values['usage_rate'] = emp_data.get('usage_rate', 0)
                    new_values['usage_rate'] = round(new_usage_rate, 2)

                # Add last_updated
                update_parts.append("last_updated = ?")
                params.append(timestamp)
                params.append(employee_id)

                # Execute update
                query = f"UPDATE employees SET {', '.join(update_parts)} WHERE id = ?"
                c.execute(query, tuple(params))

                # Record audit entries
                for field in new_values:
                    c.execute('''
                        INSERT INTO bulk_update_audit
                        (operation_id, employee_num, year, field_name, old_value, new_value, updated_by, updated_at, batch_size)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        operation_id,
                        emp_num,
                        year,
                        field,
                        str(old_values.get(field, '')),
                        str(new_values.get(field, '')),
                        updated_by,
                        timestamp,
                        len(employee_nums)
                    ))

                    results["audit_records"].append({
                        "employee_num": emp_num,
                        "field": field,
                        "old_value": old_values.get(field),
                        "new_value": new_values.get(field)
                    })

                results["updated_count"] += 1
                results["details"].append({
                    "employee_num": emp_num,
                    "name": emp_data.get('name', 'Unknown'),
                    "changes": new_values
                })

            except Exception as e:
                results["errors"].append({
                    "employee_num": emp_num,
                    "error": str(e)
                })

        conn.commit()

    results["success"] = results["updated_count"] > 0 and len(results["errors"]) == 0
    return results


def get_bulk_update_history(operation_id: str = None, employee_num: str = None,
                            limit: int = 100) -> List[Dict]:
    """
    Obtiene el historial de actualizaciones masivas.

    Args:
        operation_id: Filtrar por ID de operacion
        employee_num: Filtrar por numero de empleado
        limit: Maximo de registros a retornar

    Returns:
        Lista de registros de auditoria
    """
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM bulk_update_audit WHERE 1=1"
        params = []

        if operation_id:
            query += " AND operation_id = ?"
            params.append(operation_id)

        if employee_num:
            query += " AND employee_num = ?"
            params.append(employee_num)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        try:
            rows = c.execute(query, tuple(params)).fetchall()
            return [dict(row) for row in rows]
        except Exception:
            # Table might not exist yet
            return []


def revert_bulk_update(operation_id: str, reverted_by: str = "system") -> Dict[str, Any]:
    """
    Revierte una operacion de bulk update usando el audit trail.

    Args:
        operation_id: ID de la operacion a revertir
        reverted_by: Usuario que realiza la reversion

    Returns:
        Dict con resultados de la reversion
    """
    with get_db() as conn:
        c = conn.cursor()

        # Get all audit records for this operation
        rows = c.execute(
            "SELECT * FROM bulk_update_audit WHERE operation_id = ?",
            (operation_id,)
        ).fetchall()

        if not rows:
            raise ValueError(f"Operacion {operation_id} no encontrada en el historial")

        audit_records = [dict(row) for row in rows]
        timestamp = datetime.now().isoformat()
        reverted_count = 0
        errors = []

        # Group by employee
        employees_changes = {}
        for record in audit_records:
            emp_num = record['employee_num']
            if emp_num not in employees_changes:
                employees_changes[emp_num] = {
                    'year': record['year'],
                    'fields': {}
                }
            employees_changes[emp_num]['fields'][record['field_name']] = record['old_value']

        # Revert each employee
        for emp_num, changes in employees_changes.items():
            year = changes['year']
            employee_id = f"{emp_num}_{year}"

            try:
                update_parts = []
                params = []

                for field, old_value in changes['fields'].items():
                    if field in ['granted', 'used', 'balance', 'usage_rate']:
                        update_parts.append(f"{field} = ?")
                        params.append(float(old_value) if old_value else 0)
                    elif field == 'haken':
                        update_parts.append(f"{field} = ?")
                        params.append(old_value or '')

                if update_parts:
                    update_parts.append("last_updated = ?")
                    params.append(timestamp)
                    params.append(employee_id)

                    query = f"UPDATE employees SET {', '.join(update_parts)} WHERE id = ?"
                    c.execute(query, tuple(params))
                    reverted_count += 1

            except Exception as e:
                errors.append({
                    "employee_num": emp_num,
                    "error": str(e)
                })

        # Mark original audit records as reverted
        c.execute('''
            UPDATE bulk_update_audit
            SET updated_by = ?
            WHERE operation_id = ?
        ''', (f"REVERTED by {reverted_by}", operation_id))

        conn.commit()

        return {
            "success": reverted_count > 0,
            "reverted_count": reverted_count,
            "original_operation_id": operation_id,
            "errors": errors,
            "reverted_by": reverted_by,
            "reverted_at": timestamp
        }


# ============================================
# NOTIFICATION READ STATUS FUNCTIONS (v2.6)
# ============================================
