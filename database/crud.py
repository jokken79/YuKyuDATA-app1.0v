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
CRUD operations for all employee types and data management.
Handles: Employees, Genzai, Ukeoi, Staff, and Statistics
"""



def save_employees(employees_data):
    """
    Saves a list of employee dictionaries to the database.
    Replaces existing data for the same ID to ensure synchronization.
    Works with both SQLite and PostgreSQL.
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in employees_data:
            # Generate a consistent ID based on employee_num and year if not present
            if 'id' not in emp:
                emp['id'] = f"{emp.get('employeeNum')}_{emp.get('year')}"

            if USE_POSTGRESQL:
                # PostgreSQL: Use ON CONFLICT for upsert
                c.execute('''
                    INSERT INTO employees
                    (id, employee_num, name, haken, granted, used, balance, expired, usage_rate, year, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        employee_num = EXCLUDED.employee_num,
                        name = EXCLUDED.name,
                        haken = EXCLUDED.haken,
                        granted = EXCLUDED.granted,
                        used = EXCLUDED.used,
                        balance = EXCLUDED.balance,
                        expired = EXCLUDED.expired,
                        usage_rate = EXCLUDED.usage_rate,
                        year = EXCLUDED.year,
                        last_updated = EXCLUDED.last_updated
                ''', (
                    emp.get('id'),
                    emp.get('employeeNum'),
                    emp.get('name'),
                    emp.get('haken'),
                    emp.get('granted'),
                    emp.get('used'),
                    emp.get('balance'),
                    emp.get('expired', 0.0),
                    emp.get('usageRate'),
                    emp.get('year'),
                    timestamp
                ))
            else:
                # SQLite: Use INSERT OR REPLACE
                c.execute('''
                    INSERT OR REPLACE INTO employees
                    (id, employee_num, name, haken, granted, used, balance, expired, usage_rate, year, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    emp.get('id'),
                    emp.get('employeeNum'),
                    emp.get('name'),
                    emp.get('haken'),
                    emp.get('granted'),
                    emp.get('used'),
                    emp.get('balance'),
                    emp.get('expired', 0.0),
                    emp.get('usageRate'),
                    emp.get('year'),
                    timestamp
                ))

        conn.commit()

def get_employees(year=None):
    """Retrieves employees, optionally filtered by year."""
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM employees"
        params = []

        if year:
            query += " WHERE year = ?"
            params.append(year)

        query += " ORDER BY usage_rate DESC"

        rows = c.execute(query, params).fetchall()

        # Convert rows to list of dicts
        return [dict(row) for row in rows]

def get_available_years():
    """Returns a list of years present in the database."""
    with get_db() as conn:
        c = conn.cursor()
        rows = c.execute("SELECT DISTINCT year FROM employees ORDER BY year DESC").fetchall()
        return [row['year'] for row in rows]

def get_employees_enhanced(year=None, active_only=False):
    """
    Retrieves employees with type (genzai/ukeoi/staff) and active status.
    Crosses employees table with genzai and ukeoi to determine employment type and status.
    """
    conn = get_db_connection()
    c = conn.cursor()

    # Query with LEFT JOINs to genzai and ukeoi
    query = '''
        SELECT
            e.*,
            CASE
                WHEN g.id IS NOT NULL THEN 'genzai'
                WHEN u.id IS NOT NULL THEN 'ukeoi'
                ELSE 'staff'
            END as employee_type,
            COALESCE(g.status, u.status, '在職中') as employment_status,
            CASE
                WHEN g.status = '在職中' OR u.status = '在職中' OR (g.id IS NULL AND u.id IS NULL) THEN 1
                ELSE 0
            END as is_active
        FROM employees e
        LEFT JOIN genzai g ON e.employee_num = g.employee_num
        LEFT JOIN ukeoi u ON e.employee_num = u.employee_num
    '''

    params = []
    conditions = []

    if year:
        conditions.append("e.year = ?")
        params.append(year)

    if active_only:
        conditions.append("""
            (g.status = '在職中' OR u.status = '在職中' OR (g.id IS NULL AND u.id IS NULL))
        """)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY e.usage_rate DESC"

    rows = c.execute(query, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]

def clear_database():
    with get_db() as conn:
        conn.execute("DELETE FROM employees")
        conn.commit()

# === GENZAI (Dispatch Employees) Functions ===

def save_genzai(genzai_data):
    """Saves dispatch employee data from DBGenzaiX sheet. Works with SQLite and PostgreSQL."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in genzai_data:
            # Encrypt sensitive fields
            encrypted_birth_date = encrypt_field(emp.get('birth_date'))
            encrypted_hourly_wage = encrypt_field(str(emp.get('hourly_wage')) if emp.get('hourly_wage') else None)

            params = (
                emp.get('id'),
                emp.get('status'),
                emp.get('employee_num'),
                emp.get('dispatch_id'),
                emp.get('dispatch_name'),
                emp.get('department'),
                emp.get('line'),
                emp.get('job_content'),
                emp.get('name'),
                emp.get('kana'),
                emp.get('gender'),
                emp.get('nationality'),
                encrypted_birth_date,
                emp.get('age'),
                encrypted_hourly_wage,
                emp.get('wage_revision'),
                timestamp
            )

            if USE_POSTGRESQL:
                c.execute('''
                    INSERT INTO genzai
                    (id, status, employee_num, dispatch_id, dispatch_name, department, line,
                     job_content, name, kana, gender, nationality, birth_date, age,
                     hourly_wage, wage_revision, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        employee_num = EXCLUDED.employee_num,
                        dispatch_id = EXCLUDED.dispatch_id,
                        dispatch_name = EXCLUDED.dispatch_name,
                        department = EXCLUDED.department,
                        line = EXCLUDED.line,
                        job_content = EXCLUDED.job_content,
                        name = EXCLUDED.name,
                        kana = EXCLUDED.kana,
                        gender = EXCLUDED.gender,
                        nationality = EXCLUDED.nationality,
                        birth_date = EXCLUDED.birth_date,
                        age = EXCLUDED.age,
                        hourly_wage = EXCLUDED.hourly_wage,
                        wage_revision = EXCLUDED.wage_revision,
                        last_updated = EXCLUDED.last_updated
                ''', params)
            else:
                c.execute('''
                    INSERT OR REPLACE INTO genzai
                    (id, status, employee_num, dispatch_id, dispatch_name, department, line,
                     job_content, name, kana, gender, nationality, birth_date, age,
                     hourly_wage, wage_revision, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', params)

        conn.commit()

def get_genzai(status=None, year=None, active_in_year=False):
    """
    Retrieves dispatch employees with optional filters.

    Args:
        status: Filter by status (e.g., '在職中')
        year: Filter by fiscal year
        active_in_year: If True with year, filters employees who were active during that year
                       (hire_date <= year AND (leave_date IS NULL OR leave_date >= year))
    """
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM genzai WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if year and active_in_year:
            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"
            query += """ AND (
                (hire_date IS NULL OR hire_date <= ?)
                AND (leave_date IS NULL OR leave_date >= ?)
            )"""
            params.extend([year_end, year_start])

        query += " ORDER BY name"
        rows = c.execute(query, params).fetchall()

        # Decrypt sensitive fields
        result = []
        for row in rows:
            emp = dict(row)
            if emp.get('birth_date'):
                emp['birth_date'] = decrypt_field(emp['birth_date']) or emp['birth_date']
            if emp.get('hourly_wage'):
                try:
                    decrypted = decrypt_field(emp['hourly_wage'])
                    if decrypted:
                        emp['hourly_wage'] = int(float(decrypted))
                except (ValueError, TypeError):
                    pass
            result.append(emp)

        return result

def clear_genzai():
    """Clears genzai table."""
    with get_db() as conn:
        conn.execute("DELETE FROM genzai")
        conn.commit()

# === UKEOI (Contract Employees) Functions ===

def save_ukeoi(ukeoi_data):
    """Saves contract employee data from DBUkeoiX sheet. Works with SQLite and PostgreSQL."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in ukeoi_data:
            # Encrypt sensitive fields
            encrypted_birth_date = encrypt_field(emp.get('birth_date'))
            encrypted_hourly_wage = encrypt_field(str(emp.get('hourly_wage')) if emp.get('hourly_wage') else None)

            params = (
                emp.get('id'),
                emp.get('status'),
                emp.get('employee_num'),
                emp.get('contract_business'),
                emp.get('name'),
                emp.get('kana'),
                emp.get('gender'),
                emp.get('nationality'),
                encrypted_birth_date,
                emp.get('age'),
                encrypted_hourly_wage,
                emp.get('wage_revision'),
                timestamp
            )

            if USE_POSTGRESQL:
                c.execute('''
                    INSERT INTO ukeoi
                    (id, status, employee_num, contract_business, name, kana, gender,
                     nationality, birth_date, age, hourly_wage, wage_revision, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        employee_num = EXCLUDED.employee_num,
                        contract_business = EXCLUDED.contract_business,
                        name = EXCLUDED.name,
                        kana = EXCLUDED.kana,
                        gender = EXCLUDED.gender,
                        nationality = EXCLUDED.nationality,
                        birth_date = EXCLUDED.birth_date,
                        age = EXCLUDED.age,
                        hourly_wage = EXCLUDED.hourly_wage,
                        wage_revision = EXCLUDED.wage_revision,
                        last_updated = EXCLUDED.last_updated
                ''', params)
            else:
                c.execute('''
                    INSERT OR REPLACE INTO ukeoi
                    (id, status, employee_num, contract_business, name, kana, gender,
                     nationality, birth_date, age, hourly_wage, wage_revision, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', params)

        conn.commit()

def get_ukeoi(status=None, year=None, active_in_year=False):
    """
    Retrieves contract employees with optional filters.

    Args:
        status: Filter by status (e.g., '在職中')
        year: Filter by fiscal year
        active_in_year: If True with year, filters employees who were active during that year
    """
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM ukeoi WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if year and active_in_year:
            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"
            query += """ AND (
                (hire_date IS NULL OR hire_date <= ?)
                AND (leave_date IS NULL OR leave_date >= ?)
            )"""
            params.extend([year_end, year_start])

        query += " ORDER BY name"
        rows = c.execute(query, params).fetchall()

        # Decrypt sensitive fields
        result = []
        for row in rows:
            emp = dict(row)
            if emp.get('birth_date'):
                emp['birth_date'] = decrypt_field(emp['birth_date']) or emp['birth_date']
            if emp.get('hourly_wage'):
                try:
                    decrypted = decrypt_field(emp['hourly_wage'])
                    if decrypted:
                        emp['hourly_wage'] = int(float(decrypted))
                except (ValueError, TypeError):
                    pass
            result.append(emp)

        return result


# === STAFF Functions ===

def save_staff(staff_data):
    """Saves staff employee data from DBStaffX sheet. Works with SQLite and PostgreSQL."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in staff_data:
            # Encrypt sensitive fields
            encrypted_birth_date = encrypt_field(emp.get('birth_date'))
            encrypted_postal_code = encrypt_field(emp.get('postal_code'))
            encrypted_address = encrypt_field(emp.get('address'))
            encrypted_visa_type = encrypt_field(emp.get('visa_type'))

            params = (
                emp.get('id'),
                emp.get('status'),
                emp.get('employee_num'),
                emp.get('office'),
                emp.get('name'),
                emp.get('kana'),
                emp.get('gender'),
                emp.get('nationality'),
                encrypted_birth_date,
                emp.get('age'),
                emp.get('visa_expiry'),
                encrypted_visa_type,
                emp.get('spouse'),
                encrypted_postal_code,
                encrypted_address,
                emp.get('building'),
                emp.get('hire_date'),
                emp.get('leave_date'),
                timestamp
            )

            if USE_POSTGRESQL:
                c.execute('''
                    INSERT INTO staff
                    (id, status, employee_num, office, name, kana, gender, nationality,
                     birth_date, age, visa_expiry, visa_type, spouse, postal_code,
                     address, building, hire_date, leave_date, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        employee_num = EXCLUDED.employee_num,
                        office = EXCLUDED.office,
                        name = EXCLUDED.name,
                        kana = EXCLUDED.kana,
                        gender = EXCLUDED.gender,
                        nationality = EXCLUDED.nationality,
                        birth_date = EXCLUDED.birth_date,
                        age = EXCLUDED.age,
                        visa_expiry = EXCLUDED.visa_expiry,
                        visa_type = EXCLUDED.visa_type,
                        spouse = EXCLUDED.spouse,
                        postal_code = EXCLUDED.postal_code,
                        address = EXCLUDED.address,
                        building = EXCLUDED.building,
                        hire_date = EXCLUDED.hire_date,
                        leave_date = EXCLUDED.leave_date,
                        last_updated = EXCLUDED.last_updated
                ''', params)
            else:
                c.execute('''
                    INSERT OR REPLACE INTO staff
                    (id, status, employee_num, office, name, kana, gender, nationality,
                     birth_date, age, visa_expiry, visa_type, spouse, postal_code,
                     address, building, hire_date, leave_date, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', params)

        conn.commit()


def get_staff(status=None, year=None, active_in_year=False):
    """
    Retrieves staff employees with optional filters.

    Args:
        status: Filter by status (e.g., '在職中')
        year: Filter by fiscal year
        active_in_year: If True with year, filters employees who were active during that year
    """
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM staff WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if year and active_in_year:
            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31"
            query += """ AND (
                (hire_date IS NULL OR hire_date <= ?)
                AND (leave_date IS NULL OR leave_date >= ?)
            )"""
            params.extend([year_end, year_start])

        query += " ORDER BY name"
        rows = c.execute(query, params).fetchall()

        # Decrypt sensitive fields
        result = []
        for row in rows:
            emp = dict(row)
            if emp.get('birth_date'):
                emp['birth_date'] = decrypt_field(emp['birth_date']) or emp['birth_date']
            if emp.get('postal_code'):
                emp['postal_code'] = decrypt_field(emp['postal_code']) or emp['postal_code']
            if emp.get('address'):
                emp['address'] = decrypt_field(emp['address']) or emp['address']
            if emp.get('visa_type'):
                emp['visa_type'] = decrypt_field(emp['visa_type']) or emp['visa_type']
            result.append(emp)

        return result


def clear_staff():
    """Clears staff table."""
    with get_db() as conn:
        conn.execute("DELETE FROM staff")
        conn.commit()

def clear_ukeoi():
    """Clears ukeoi table."""
    with get_db() as conn:
        conn.execute("DELETE FROM ukeoi")
        conn.commit()

# === STATISTICS Functions ===
