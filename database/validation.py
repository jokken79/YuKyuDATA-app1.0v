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
Validation functions for database operations.
Ensures business logic constraints (balance limits, etc)
"""

from database.connection import get_db

# Constants
MAX_ACCUMULATED_DAYS = 40



def validate_balance_limit(employee_num: str, year: int, additional_days: float = 0) -> bool:
    """
    Verifica que el balance total no exceda 40 días.
    Lanza ValueError si se excede el límite.

    Args:
        employee_num: Número de empleado
        year: Año fiscal actual
        additional_days: Días adicionales a agregar (para validar antes de operaciones)

    Returns:
        True si el balance está dentro del límite

    Raises:
        ValueError: Si el balance excede el límite de 40 días
    """
    with get_db() as conn:
        c = conn.cursor()
        # Sumar balance de año actual y año anterior (máximo 2 años carry-over)
        c.execute('''
            SELECT COALESCE(SUM(balance), 0) as total_balance
            FROM employees
            WHERE employee_num = ? AND year >= ?
        ''', (employee_num, year - 1))
        result = c.fetchone()
        current_balance = result['total_balance'] if result else 0
        total = current_balance + additional_days

        if total > MAX_ACCUMULATED_DAYS:
            raise ValueError(
                f"Balance excede límite de {MAX_ACCUMULATED_DAYS} días: {total:.1f} días. "
                f"Balance actual: {current_balance:.1f}, adicional: {additional_days:.1f}"
            )
        return True


def get_employee_total_balance(employee_num: str, year: int) -> float:
    """
    Obtiene el balance total de un empleado (año actual + anterior).
    Útil para validaciones antes de operaciones.

    Args:
        employee_num: Número de empleado
        year: Año fiscal actual

    Returns:
        Balance total acumulado
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT COALESCE(SUM(balance), 0) as total_balance
            FROM employees
            WHERE employee_num = ? AND year >= ?
        ''', (employee_num, year - 1))
        result = c.fetchone()
        return result['total_balance'] if result else 0.0
