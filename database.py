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
    with get_db() as conn:
        c = conn.cursor()

        # Create Employees table (vacation data)
        c.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                employee_num TEXT,
                name TEXT,
                haken TEXT,
                granted REAL,
                used REAL,
                balance REAL,
                expired REAL,
                usage_rate REAL,
                year INTEGER,
                last_updated TEXT
            )
        ''')

        # Create Yukyu Usage Details table (individual usage dates - like v2.0)
        c.execute('''
            CREATE TABLE IF NOT EXISTS yukyu_usage_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT,
                name TEXT,
                use_date TEXT,
                year INTEGER,
                month INTEGER,
                days_used REAL DEFAULT 1.0,
                last_updated TEXT,
                UNIQUE(employee_num, use_date)
            )
        ''')

        # Create index for fast lookups
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_usage_employee_year
            ON yukyu_usage_details(employee_num, year)
        ''')

        # Create Genzai table (current dispatch employees - DBGenzaiX)
        c.execute('''
            CREATE TABLE IF NOT EXISTS genzai (
                id TEXT PRIMARY KEY,
                status TEXT,
                employee_num TEXT,
                dispatch_id TEXT,
                dispatch_name TEXT,
                department TEXT,
                line TEXT,
                job_content TEXT,
                name TEXT,
                kana TEXT,
                gender TEXT,
                nationality TEXT,
                birth_date TEXT,
                age INTEGER,
                hourly_wage INTEGER,
                wage_revision TEXT,
                last_updated TEXT
            )
        ''')

        # Create Ukeoi table (contract employees - DBUkeoiX)
        c.execute('''
            CREATE TABLE IF NOT EXISTS ukeoi (
                id TEXT PRIMARY KEY,
                status TEXT,
                employee_num TEXT,
                contract_business TEXT,
                name TEXT,
                kana TEXT,
                gender TEXT,
                nationality TEXT,
                birth_date TEXT,
                age INTEGER,
                hourly_wage INTEGER,
                wage_revision TEXT,
                last_updated TEXT
            )
        ''')

        # Create Leave Requests table (yukyu solicitudes)
        c.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT NOT NULL,
                employee_name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                days_requested REAL NOT NULL,
                hours_requested REAL DEFAULT 0,
                leave_type TEXT DEFAULT 'full',
                reason TEXT,
                status TEXT DEFAULT 'PENDING',
                requested_at TEXT NOT NULL,
                approved_by TEXT,
                approved_at TEXT,
                year INTEGER NOT NULL,
                hourly_wage INTEGER DEFAULT 0,
                cost_estimate REAL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        ''')

        # ============================================
        # STRATEGIC INDEXES FOR PERFORMANCE
        # ============================================

        # Indexes for employees table
        c.execute('CREATE INDEX IF NOT EXISTS idx_emp_num ON employees(employee_num)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_emp_year ON employees(year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_emp_num_year ON employees(employee_num, year)')
        # ✅ FIX 5/6: Add index for 5-day compliance queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_employees_granted ON employees(year, granted)')

        # Indexes for leave_requests table
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_emp_num ON leave_requests(employee_num)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_status ON leave_requests(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_year ON leave_requests(year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_dates ON leave_requests(start_date, end_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_employee_date ON leave_requests(employee_num, start_date)')

        # Indexes for genzai/ukeoi tables (basic - columns always exist)
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_emp ON genzai(employee_num)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_status ON genzai(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ukeoi_emp ON ukeoi(employee_num)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ukeoi_status ON ukeoi(status)')

        # ============================================
        # SCHEMA MIGRATIONS (add columns if not exist)
        # ============================================

        # Add hire_date to genzai if not exists
        try:
            c.execute("ALTER TABLE genzai ADD COLUMN hire_date TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add leave_date to genzai if not exists
        try:
            c.execute("ALTER TABLE genzai ADD COLUMN leave_date TEXT")
        except sqlite3.OperationalError:
            pass

        # Add hire_date to ukeoi if not exists
        try:
            c.execute("ALTER TABLE ukeoi ADD COLUMN hire_date TEXT")
        except sqlite3.OperationalError:
            pass

        # Add leave_date to ukeoi if not exists
        try:
            c.execute("ALTER TABLE ukeoi ADD COLUMN leave_date TEXT")
        except sqlite3.OperationalError:
            pass

        # Create indexes on hire_date/leave_date (after columns are added)
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_hire_date ON genzai(hire_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_leave_date ON genzai(leave_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_hire_leave ON genzai(hire_date, leave_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_status_hire ON genzai(status, hire_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ukeoi_hire_date ON ukeoi(hire_date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ukeoi_leave_date ON ukeoi(leave_date)')

        # Create Staff table if not exists
        c.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id TEXT PRIMARY KEY,
                status TEXT,
                employee_num TEXT,
                office TEXT,
                name TEXT,
                kana TEXT,
                gender TEXT,
                nationality TEXT,
                birth_date TEXT,
                age INTEGER,
                visa_expiry TEXT,
                visa_type TEXT,
                spouse TEXT,
                postal_code TEXT,
                address TEXT,
                building TEXT,
                hire_date TEXT,
                leave_date TEXT,
                last_updated TEXT
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_staff_emp ON staff(employee_num)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_staff_status ON staff(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_staff_visa_expiry ON staff(visa_expiry)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_staff_visa_type ON staff(visa_type)')

        # Add grant_year to employees for LIFO tracking
        try:
            c.execute("ALTER TABLE employees ADD COLUMN grant_year INTEGER")
        except sqlite3.OperationalError:
            pass

        # ============================================
        # AUDIT LOG TABLE (v2.3 - Complete Audit Trail)
        # ============================================
        c.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                user_agent TEXT,
                additional_info TEXT
            )
        ''')

        # Indexes for fast audit log queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)')

        # ============================================
        # NOTIFICATION READS TABLE (v2.6 - Track Read Status)
        # ============================================
        c.execute('''
            CREATE TABLE IF NOT EXISTS notification_reads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                read_at TEXT NOT NULL,
                UNIQUE(notification_id, user_id)
            )
        ''')

        # Index for fast lookup
        c.execute('CREATE INDEX IF NOT EXISTS idx_notif_reads_user ON notification_reads(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notif_reads_notif ON notification_reads(notification_id)')

        # ============================================
        # REFRESH TOKENS TABLE (v5.17 - Secure Token Storage)
        # ============================================
        c.execute('''
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                revoked INTEGER DEFAULT 0,
                revoked_at TEXT,
                user_agent TEXT,
                ip_address TEXT
            )
        ''')

        # Indices para refresh_tokens
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked ON refresh_tokens(revoked)')

        # ============================================
        # FISCAL YEAR COMPLIANCE AUDIT (v5.20 - Legal Compliance)
        # ============================================

        # Fiscal Year Audit Log - Registro de todas las operaciones fiscales
        c.execute('''
            CREATE TABLE IF NOT EXISTS fiscal_year_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                employee_num TEXT NOT NULL,
                year INTEGER NOT NULL,
                days_affected REAL,
                balance_before REAL,
                balance_after REAL,
                performed_by TEXT,
                reason TEXT,
                timestamp TEXT NOT NULL,
                UNIQUE(employee_num, year, action, timestamp)
            )
        ''')

        # Indexes for fiscal_year_audit_log
        c.execute('CREATE INDEX IF NOT EXISTS idx_fiscal_audit_emp_year ON fiscal_year_audit_log(employee_num, year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_fiscal_audit_action ON fiscal_year_audit_log(action)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_fiscal_audit_timestamp ON fiscal_year_audit_log(timestamp)')

        # Official Leave Designation - 企業による5日の指定
        c.execute('''
            CREATE TABLE IF NOT EXISTS official_leave_designation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT NOT NULL,
                year INTEGER NOT NULL,
                designated_date TEXT NOT NULL,
                days REAL DEFAULT 1.0,
                reason TEXT,
                designated_by TEXT,
                designated_at TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                UNIQUE(employee_num, year, designated_date)
            )
        ''')

        # Indexes for official_leave_designation
        c.execute('CREATE INDEX IF NOT EXISTS idx_official_leave_emp_year ON official_leave_designation(employee_num, year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_official_leave_status ON official_leave_designation(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_official_leave_date ON official_leave_designation(designated_date)')

        # Carry-Over Audit - Registro de traspasos de año
        c.execute('''
            CREATE TABLE IF NOT EXISTS carryover_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_year INTEGER NOT NULL,
                to_year INTEGER NOT NULL,
                employee_num TEXT NOT NULL,
                days_carried_over REAL,
                days_expired REAL,
                days_capped REAL,
                executed_at TEXT NOT NULL,
                executed_by TEXT,
                executed_reason TEXT,
                UNIQUE(from_year, to_year, employee_num)
            )
        ''')

        # Indexes for carryover_audit
        c.execute('CREATE INDEX IF NOT EXISTS idx_carryover_years ON carryover_audit(from_year, to_year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_carryover_emp ON carryover_audit(employee_num)')

        conn.commit()


# ============================================
# BALANCE LIMIT VALIDATION (Japanese Labor Law)
# Maximum accumulated days: 40 (2 years carry-over max)
# ============================================

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

def get_stats_by_factory(year=None):
    """Returns vacation usage statistics grouped by factory (派遣先/haken)."""
    with get_db() as conn:
        c = conn.cursor()

        query = """
            SELECT
                haken,
                COUNT(DISTINCT employee_num) as employee_count,
                SUM(used) as total_used,
                SUM(granted) as total_granted,
                SUM(balance) as total_balance,
                GROUP_CONCAT(name || '|' || employee_num || '|' || used || '|' || granted || '|' || balance || '|' || year, '::') as employees
            FROM employees
        """

        params = []
        if year:
            query += " WHERE year = ?"
            params.append(year)

        query += """
            GROUP BY haken
            ORDER BY total_used DESC
        """

        rows = c.execute(query, params).fetchall()

        # Process results
        result = []
        for row in rows:
            # Parse employee details
            employees = []
            if row['employees']:
                for emp_str in row['employees'].split('::'):
                    parts = emp_str.split('|')
                    if len(parts) >= 6:
                        employees.append({
                            'name': parts[0],
                            'employee_num': parts[1],
                            'used': float(parts[2]),
                            'granted': float(parts[3]),
                            'balance': float(parts[4]),
                            'year': int(float(parts[5]))
                        })

            result.append({
                'factory': row['haken'] if row['haken'] else 'Unknown',
                'employee_count': row['employee_count'],
                'total_used': round(row['total_used'], 1) if row['total_used'] else 0,
                'total_granted': round(row['total_granted'], 1) if row['total_granted'] else 0,
                'total_balance': round(row['total_balance'], 1) if row['total_balance'] else 0,
                'employees': employees
            })

        return result

# === LEAVE REQUESTS Functions ===

# ✅ FIX 4: Optimized query to get hourly wage - O(1) instead of O(n)
def get_employee_hourly_wage(employee_num: str) -> float:
    """
    Get hourly wage from genzai or ukeoi - O(1) query instead of N+1.

    Returns:
        float: Hourly wage or 0 if not found
    """
    with get_db() as conn:
        c = conn.cursor()

        # Check genzai first
        emp = c.execute(
            "SELECT hourly_wage FROM genzai WHERE employee_num = ? LIMIT 1",
            (employee_num,)
        ).fetchone()

        if emp and emp['hourly_wage']:
            return float(emp['hourly_wage'])

        # Check ukeoi if not found in genzai
        emp = c.execute(
            "SELECT hourly_wage FROM ukeoi WHERE employee_num = ? LIMIT 1",
            (employee_num,)
        ).fetchone()

        return float(emp['hourly_wage']) if emp and emp['hourly_wage'] else 0.0


def create_leave_request(employee_num, employee_name, start_date, end_date, days_requested, reason, year,
                         hours_requested=0, leave_type='full', hourly_wage=0):
    """Creates a new leave request (yukyu solicitud). Works with SQLite and PostgreSQL.

    Args:
        employee_num: 社員番号
        employee_name: 氏名
        start_date: 開始日
        end_date: 終了日
        days_requested: 申請日数
        reason: 理由
        year: 年度
        hours_requested: 申請時間 (時間単位有給用)
        leave_type: 種類 (full/half_am/half_pm/hourly)
        hourly_wage: 時給 (コスト計算用)
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Calculate cost estimate
        # 1 day = 8 hours typical
        total_hours = (days_requested * 8) + hours_requested
        cost_estimate = total_hours * hourly_wage if hourly_wage > 0 else 0

        if USE_POSTGRESQL:
            c.execute('''
                INSERT INTO leave_requests
                (employee_num, employee_name, start_date, end_date, days_requested, hours_requested,
                 leave_type, reason, status, requested_at, year, hourly_wage, cost_estimate, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING', %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (employee_num, employee_name, start_date, end_date, days_requested, hours_requested,
                  leave_type, reason, timestamp, year, hourly_wage, cost_estimate, timestamp, timestamp))
            request_id = c.fetchone()[0]
        else:
            c.execute('''
                INSERT INTO leave_requests
                (employee_num, employee_name, start_date, end_date, days_requested, hours_requested,
                 leave_type, reason, status, requested_at, year, hourly_wage, cost_estimate, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
            ''', (employee_num, employee_name, start_date, end_date, days_requested, hours_requested,
                  leave_type, reason, timestamp, year, hourly_wage, cost_estimate, timestamp))
            request_id = c.lastrowid

        conn.commit()
        return request_id

def get_leave_requests(status=None, employee_num=None, year=None):
    """Retrieves leave requests with optional filters."""
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM leave_requests WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if employee_num:
            query += " AND employee_num = ?"
            params.append(employee_num)

        if year:
            query += " AND year = ?"
            params.append(year)

        query += " ORDER BY created_at DESC"

        rows = c.execute(query, params).fetchall()
        return [dict(row) for row in rows]

def approve_leave_request(request_id, approved_by):
    """Approves a leave request and updates employee yukyu balance."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Get request details
        request = c.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()

        if not request:
            raise ValueError(f"Request {request_id} not found")

        if request['status'] != 'PENDING':
            raise ValueError(f"Request {request_id} is not pending (current status: {request['status']})")

        # Update request status
        c.execute('''
            UPDATE leave_requests
            SET status = 'APPROVED', approved_by = ?, approved_at = ?
            WHERE id = ?
        ''', (approved_by, timestamp, request_id))

        # Update employee yukyu balance (add to used days)
        employee_id = f"{request['employee_num']}_{request['year']}"

        # Get current employee record
        employee = c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()

        if employee:
            new_used = employee['used'] + request['days_requested']
            new_balance = employee['granted'] - new_used
            new_usage_rate = round((new_used / employee['granted']) * 100) if employee['granted'] > 0 else 0

            c.execute('''
                UPDATE employees
                SET used = ?, balance = ?, usage_rate = ?, last_updated = ?
                WHERE id = ?
            ''', (new_used, new_balance, new_usage_rate, timestamp, employee_id))

        conn.commit()
        return True

def reject_leave_request(request_id, approved_by):
    """Rejects a leave request."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Check if request exists and is pending
        request = c.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()

        if not request:
            raise ValueError(f"Request {request_id} not found")

        if request['status'] != 'PENDING':
            raise ValueError(f"Request {request_id} is not pending")

        # Update request status
        c.execute('''
            UPDATE leave_requests
            SET status = 'REJECTED', approved_by = ?, approved_at = ?
            WHERE id = ?
        ''', (approved_by, timestamp, request_id))

        conn.commit()
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


def revert_approved_request(request_id, reverted_by="Manager"):
    """
    Revierte una solicitud YA APROBADA.
    Devuelve los días usados al balance del empleado.

    Args:
        request_id: ID de la solicitud
        reverted_by: Quién revierte la solicitud

    Returns:
        dict con info de la reversión
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Get request details
        request = c.execute("SELECT * FROM leave_requests WHERE id = ?", (request_id,)).fetchone()

        if not request:
            raise ValueError(f"Solicitud {request_id} no encontrada")

        if request['status'] != 'APPROVED':
            raise ValueError(f"Solo se pueden revertir solicitudes aprobadas. Estado actual: {request['status']}")

        # Update request status to CANCELLED
        c.execute('''
            UPDATE leave_requests
            SET status = 'CANCELLED', approved_by = ?, approved_at = ?
            WHERE id = ?
        ''', (f"REVERTED by {reverted_by}", timestamp, request_id))

        # Revert employee yukyu balance (subtract from used days)
        employee_id = f"{request['employee_num']}_{request['year']}"

        employee = c.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()

        days_returned = 0
        if employee:
            days_returned = request['days_requested']
            new_used = max(0, employee['used'] - days_returned)  # No negative
            new_balance = employee['granted'] - new_used
            new_usage_rate = round((new_used / employee['granted']) * 100) if employee['granted'] > 0 else 0

            c.execute('''
                UPDATE employees
                SET used = ?, balance = ?, usage_rate = ?, last_updated = ?
                WHERE id = ?
            ''', (new_used, new_balance, new_usage_rate, timestamp, employee_id))

        conn.commit()

        return {
            "request_id": request_id,
            "employee_num": request['employee_num'],
            "employee_name": request['employee_name'],
            "days_returned": days_returned,
            "reverted_by": reverted_by
        }


# ============================================
# BACKUP & RESTORE FUNCTIONS
# ============================================

def create_backup(backup_dir="backups"):
    """
    Crea una copia de seguridad de la base de datos.

    Args:
        backup_dir: Directorio donde guardar backups

    Returns:
        dict con info del backup
    """
    import shutil

    # Create backup directory if not exists
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"yukyu_backup_{timestamp}.db"
    backup_filepath = backup_path / backup_filename

    # Copy database file
    if not Path(DB_NAME).exists():
        raise ValueError(f"Database file {DB_NAME} not found")

    shutil.copy2(DB_NAME, backup_filepath)

    # Get backup file size
    file_size = backup_filepath.stat().st_size

    # Clean old backups (keep last 10)
    backups = sorted(backup_path.glob("yukyu_backup_*.db"), reverse=True)
    for old_backup in backups[10:]:
        old_backup.unlink()

    return {
        "filename": backup_filename,
        "path": str(backup_filepath),
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "created_at": timestamp
    }


def list_backups(backup_dir="backups"):
    """
    Lista todos los backups disponibles.

    Returns:
        Lista de backups con info
    """
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        return []

    backups = []
    for backup_file in sorted(backup_path.glob("yukyu_backup_*.db"), reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "path": str(backup_file),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return backups


def restore_backup(backup_filename, backup_dir="backups"):
    """
    Restaura la base de datos desde un backup.
    CUIDADO: Esto sobrescribe la base de datos actual.

    Args:
        backup_filename: Nombre del archivo de backup
        backup_dir: Directorio de backups

    Returns:
        dict con info de la restauración
    """
    import shutil

    backup_path = Path(backup_dir) / backup_filename

    if not backup_path.exists():
        raise ValueError(f"Backup file {backup_filename} not found")

    # Create a backup of current DB before restoring
    current_backup = create_backup(backup_dir)

    # Restore the backup
    shutil.copy2(backup_path, DB_NAME)

    return {
        "restored_from": backup_filename,
        "previous_backup": current_backup['filename'],
        "restored_at": datetime.now().isoformat()
    }


# ============================================
# AUDIT LOG FUNCTIONS (v2.3 - Complete Audit Trail)
# ============================================

def log_audit(
    action: str,
    entity_type: str,
    entity_id: str = None,
    old_value: Any = None,
    new_value: Any = None,
    user_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    additional_info: Dict = None
) -> int:
    """
    Registra una accion en el audit log.

    Args:
        action: Tipo de accion (CREATE, UPDATE, DELETE, APPROVE, REJECT, REVERT, LOGIN, etc.)
        entity_type: Tipo de entidad (employee, leave_request, yukyu_usage, genzai, ukeoi, etc.)
        entity_id: ID de la entidad afectada
        old_value: Valor anterior (dict o cualquier valor serializable a JSON)
        new_value: Nuevo valor (dict o cualquier valor serializable a JSON)
        user_id: ID del usuario que realizo la accion
        ip_address: Direccion IP del cliente
        user_agent: User-Agent del navegador
        additional_info: Informacion adicional (dict)

    Returns:
        ID del registro de audit creado
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Serializar valores a JSON si son diccionarios o listas
        old_value_json = json.dumps(old_value, ensure_ascii=False, default=str) if old_value is not None else None
        new_value_json = json.dumps(new_value, ensure_ascii=False, default=str) if new_value is not None else None
        additional_info_json = json.dumps(additional_info, ensure_ascii=False, default=str) if additional_info else None

        if USE_POSTGRESQL:
            c.execute('''
                INSERT INTO audit_log
                (timestamp, user_id, action, entity_type, entity_id, old_value, new_value, ip_address, user_agent, additional_info)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (timestamp, user_id, action, entity_type, entity_id, old_value_json, new_value_json, ip_address, user_agent, additional_info_json))
            audit_id = c.fetchone()[0]
        else:
            c.execute('''
                INSERT INTO audit_log
                (timestamp, user_id, action, entity_type, entity_id, old_value, new_value, ip_address, user_agent, additional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, user_id, action, entity_type, entity_id, old_value_json, new_value_json, ip_address, user_agent, additional_info_json))
            audit_id = c.lastrowid

        conn.commit()
        return audit_id


def get_audit_log(
    entity_type: str = None,
    entity_id: str = None,
    action: str = None,
    user_id: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """
    Obtiene registros del audit log con filtros opcionales.

    Args:
        entity_type: Filtrar por tipo de entidad
        entity_id: Filtrar por ID de entidad
        action: Filtrar por tipo de accion
        user_id: Filtrar por usuario
        start_date: Fecha inicio (YYYY-MM-DD)
        end_date: Fecha fin (YYYY-MM-DD)
        limit: Maximo de registros a retornar
        offset: Offset para paginacion

    Returns:
        Lista de registros de audit
    """
    with get_db() as conn:
        c = conn.cursor()

        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)

        if action:
            query += " AND action = ?"
            params.append(action)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date + "T23:59:59")

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = c.execute(query, tuple(params)).fetchall()

        # Parsear JSON en old_value y new_value
        result = []
        for row in rows:
            record = dict(row)
            if record.get('old_value'):
                try:
                    record['old_value'] = json.loads(record['old_value'])
                except (json.JSONDecodeError, TypeError):
                    pass
            if record.get('new_value'):
                try:
                    record['new_value'] = json.loads(record['new_value'])
                except (json.JSONDecodeError, TypeError):
                    pass
            if record.get('additional_info'):
                try:
                    record['additional_info'] = json.loads(record['additional_info'])
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(record)

        return result


def get_audit_log_by_user(user_id: str, limit: int = 100) -> List[Dict]:
    """
    Obtiene todos los registros de audit de un usuario especifico.

    Args:
        user_id: ID del usuario
        limit: Maximo de registros a retornar

    Returns:
        Lista de registros de audit del usuario
    """
    return get_audit_log(user_id=user_id, limit=limit)


def get_entity_history(entity_type: str, entity_id: str, limit: int = 50) -> List[Dict]:
    """
    Obtiene el historial completo de cambios de una entidad.

    Args:
        entity_type: Tipo de entidad
        entity_id: ID de la entidad
        limit: Maximo de registros

    Returns:
        Lista de cambios ordenados por fecha (mas reciente primero)
    """
    return get_audit_log(entity_type=entity_type, entity_id=entity_id, limit=limit)


def get_audit_stats(days: int = 30) -> Dict:
    """
    Obtiene estadisticas del audit log.

    Args:
        days: Numero de dias hacia atras para calcular estadisticas

    Returns:
        Dict con estadisticas de auditoría
    """
    with get_db() as conn:
        c = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        # Conteo por tipo de accion
        actions_query = """
            SELECT action, COUNT(*) as count
            FROM audit_log
            WHERE timestamp >= ?
            GROUP BY action
            ORDER BY count DESC
        """
        action_rows = c.execute(actions_query, (cutoff_date,)).fetchall()
        actions = {row['action']: row['count'] for row in action_rows}

        # Conteo por tipo de entidad
        entities_query = """
            SELECT entity_type, COUNT(*) as count
            FROM audit_log
            WHERE timestamp >= ?
            GROUP BY entity_type
            ORDER BY count DESC
        """
        entity_rows = c.execute(entities_query, (cutoff_date,)).fetchall()
        entities = {row['entity_type']: row['count'] for row in entity_rows}

        # Conteo por usuario
        users_query = """
            SELECT user_id, COUNT(*) as count
            FROM audit_log
            WHERE timestamp >= ? AND user_id IS NOT NULL
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
        """
        user_rows = c.execute(users_query, (cutoff_date,)).fetchall()
        top_users = {row['user_id']: row['count'] for row in user_rows}

        # Total de registros
        total = c.execute(
            "SELECT COUNT(*) as total FROM audit_log WHERE timestamp >= ?",
            (cutoff_date,)
        ).fetchone()['total']

        return {
            "period_days": days,
            "total_records": total,
            "by_action": actions,
            "by_entity_type": entities,
            "top_users": top_users
        }


def cleanup_old_audit_logs(days_to_keep: int = 365) -> int:
    """
    Elimina registros de audit log mas antiguos que el numero de dias especificado.

    Args:
        days_to_keep: Numero de dias a mantener (por defecto 365 = 1 año)

    Returns:
        Numero de registros eliminados
    """
    with get_db() as conn:
        c = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        c.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff_date,))
        deleted_count = c.rowcount

        conn.commit()
        return deleted_count


# ============================================
# BULK UPDATE FUNCTIONS (v2.3 - Bulk Edit Feature)
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

def mark_notification_read(notification_id: str, user_id: str) -> bool:
    """
    Marca una notificación como leída para un usuario específico.

    Args:
        notification_id: ID de la notificación
        user_id: ID del usuario

    Returns:
        True si se marcó correctamente, False si ya estaba marcada
    """
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO notification_reads (notification_id, user_id, read_at)
                VALUES (?, ?, ?)
            ''', (notification_id, user_id, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Ya estaba marcada como leída (UNIQUE constraint)
            return False


def mark_all_notifications_read(user_id: str, notification_ids: list) -> int:
    """
    Marca múltiples notificaciones como leídas para un usuario.

    Args:
        user_id: ID del usuario
        notification_ids: Lista de IDs de notificaciones

    Returns:
        Número de notificaciones marcadas como leídas
    """
    if not notification_ids:
        return 0

    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        marked_count = 0

        for notif_id in notification_ids:
            try:
                c.execute('''
                    INSERT INTO notification_reads (notification_id, user_id, read_at)
                    VALUES (?, ?, ?)
                ''', (notif_id, user_id, timestamp))
                marked_count += 1
            except sqlite3.IntegrityError:
                # Ya estaba marcada
                pass

        conn.commit()
        return marked_count


def is_notification_read(notification_id: str, user_id: str) -> bool:
    """
    Verifica si una notificación ha sido leída por un usuario.

    Args:
        notification_id: ID de la notificación
        user_id: ID del usuario

    Returns:
        True si está leída, False si no
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 1 FROM notification_reads
            WHERE notification_id = ? AND user_id = ?
        ''', (notification_id, user_id))
        return c.fetchone() is not None


def get_read_notification_ids(user_id: str) -> set:
    """
    Obtiene todos los IDs de notificaciones leídas por un usuario.

    Args:
        user_id: ID del usuario

    Returns:
        Set de notification_ids que han sido leídas
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT notification_id FROM notification_reads
            WHERE user_id = ?
        ''', (user_id,))
        return {row['notification_id'] for row in c.fetchall()}


def get_unread_count(user_id: str, notification_ids: list) -> int:
    """
    Cuenta cuántas notificaciones no han sido leídas por un usuario.

    Args:
        user_id: ID del usuario
        notification_ids: Lista de IDs de notificaciones a verificar

    Returns:
        Número de notificaciones no leídas
    """
    if not notification_ids:
        return 0

    read_ids = get_read_notification_ids(user_id)
    return len([nid for nid in notification_ids if nid not in read_ids])


# ============================================
# REFRESH TOKENS TABLE & FUNCTIONS (v5.17)
# Secure token storage with database persistence
# ============================================

def init_refresh_tokens_table():
    """
    Crea la tabla refresh_tokens para almacenamiento seguro de tokens.
    Los refresh tokens se almacenan hasheados para mayor seguridad.
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                revoked INTEGER DEFAULT 0,
                revoked_at TEXT,
                user_agent TEXT,
                ip_address TEXT
            )
        ''')

        # Indices para búsquedas eficientes
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked ON refresh_tokens(revoked)')

        conn.commit()


def store_refresh_token(
    token_id: str,
    user_id: str,
    token_hash: str,
    expires_at: str,
    user_agent: str = None,
    ip_address: str = None
) -> bool:
    """
    Almacena un nuevo refresh token en la base de datos.

    Args:
        token_id: ID único del token (UUID)
        user_id: ID del usuario al que pertenece el token
        token_hash: Hash SHA-256 del token (nunca almacenar el token plano)
        expires_at: Fecha de expiración en formato ISO
        user_agent: User-Agent del cliente (opcional)
        ip_address: IP del cliente (opcional)

    Returns:
        True si se almacenó correctamente
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        try:
            if USE_POSTGRESQL:
                c.execute('''
                    INSERT INTO refresh_tokens
                    (id, user_id, token_hash, expires_at, created_at, user_agent, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (token_id, user_id, token_hash, expires_at, timestamp, user_agent, ip_address))
            else:
                c.execute('''
                    INSERT INTO refresh_tokens
                    (id, user_id, token_hash, expires_at, created_at, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (token_id, user_id, token_hash, expires_at, timestamp, user_agent, ip_address))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error storing refresh token: {e}")
            return False


def get_refresh_token_by_hash(token_hash: str) -> Optional[Dict]:
    """
    Busca un refresh token por su hash.

    Args:
        token_hash: Hash SHA-256 del token

    Returns:
        Dict con los datos del token o None si no existe
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            SELECT * FROM refresh_tokens
            WHERE token_hash = ? AND revoked = 0
        ''', (token_hash,))

        row = c.fetchone()
        if row:
            return dict(row)
        return None


def get_refresh_token_by_id(token_id: str) -> Optional[Dict]:
    """
    Busca un refresh token por su ID.

    Args:
        token_id: ID del token

    Returns:
        Dict con los datos del token o None si no existe
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('SELECT * FROM refresh_tokens WHERE id = ?', (token_id,))

        row = c.fetchone()
        if row:
            return dict(row)
        return None


def revoke_refresh_token(token_hash: str) -> bool:
    """
    Revoca un refresh token específico.

    Args:
        token_hash: Hash del token a revocar

    Returns:
        True si se revocó correctamente
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        c.execute('''
            UPDATE refresh_tokens
            SET revoked = 1, revoked_at = ?
            WHERE token_hash = ? AND revoked = 0
        ''', (timestamp, token_hash))

        conn.commit()
        return c.rowcount > 0


def revoke_refresh_token_by_id(token_id: str) -> bool:
    """
    Revoca un refresh token por su ID.

    Args:
        token_id: ID del token a revocar

    Returns:
        True si se revocó correctamente
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        c.execute('''
            UPDATE refresh_tokens
            SET revoked = 1, revoked_at = ?
            WHERE id = ? AND revoked = 0
        ''', (timestamp, token_id))

        conn.commit()
        return c.rowcount > 0


def revoke_all_user_refresh_tokens(user_id: str) -> int:
    """
    Revoca todos los refresh tokens de un usuario (logout de todas las sesiones).

    Args:
        user_id: ID del usuario

    Returns:
        Número de tokens revocados
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        c.execute('''
            UPDATE refresh_tokens
            SET revoked = 1, revoked_at = ?
            WHERE user_id = ? AND revoked = 0
        ''', (timestamp, user_id))

        revoked_count = c.rowcount
        conn.commit()
        return revoked_count


def get_user_active_refresh_tokens(user_id: str) -> List[Dict]:
    """
    Obtiene todos los refresh tokens activos de un usuario.

    Args:
        user_id: ID del usuario

    Returns:
        Lista de tokens activos (sin el hash por seguridad)
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            SELECT id, user_id, expires_at, created_at, user_agent, ip_address
            FROM refresh_tokens
            WHERE user_id = ? AND revoked = 0 AND expires_at > ?
            ORDER BY created_at DESC
        ''', (user_id, datetime.now().isoformat()))

        rows = c.fetchall()
        return [dict(row) for row in rows]


def cleanup_expired_refresh_tokens() -> int:
    """
    Elimina todos los refresh tokens expirados o revocados.
    Debe ejecutarse periódicamente (ej: cada hora o diariamente).

    Returns:
        Número de tokens eliminados
    """
    with get_db() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()

        # Eliminar tokens expirados (más de 7 días después de expiración)
        # o tokens revocados hace más de 24 horas
        cutoff_date = (datetime.now() - timedelta(days=1)).isoformat()

        c.execute('''
            DELETE FROM refresh_tokens
            WHERE expires_at < ? OR (revoked = 1 AND revoked_at < ?)
        ''', (now, cutoff_date))

        deleted_count = c.rowcount
        conn.commit()
        return deleted_count


def is_refresh_token_valid(token_hash: str) -> bool:
    """
    Verifica si un refresh token es válido (existe, no revocado, no expirado).

    Args:
        token_hash: Hash del token

    Returns:
        True si el token es válido
    """
    with get_db() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()

        c.execute('''
            SELECT 1 FROM refresh_tokens
            WHERE token_hash = ? AND revoked = 0 AND expires_at > ?
        ''', (token_hash, now))

        return c.fetchone() is not None


def get_refresh_token_stats() -> Dict:
    """
    Obtiene estadísticas de los refresh tokens.

    Returns:
        Dict con estadísticas (total, activos, revocados, expirados)
    """
    with get_db() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()

        # Total de tokens
        c.execute('SELECT COUNT(*) as count FROM refresh_tokens')
        total = c.fetchone()['count']

        # Tokens activos
        c.execute('''
            SELECT COUNT(*) as count FROM refresh_tokens
            WHERE revoked = 0 AND expires_at > ?
        ''', (now,))
        active = c.fetchone()['count']

        # Tokens revocados
        c.execute('SELECT COUNT(*) as count FROM refresh_tokens WHERE revoked = 1')
        revoked = c.fetchone()['count']

        # Tokens expirados (no revocados pero expirados)
        c.execute('''
            SELECT COUNT(*) as count FROM refresh_tokens
            WHERE revoked = 0 AND expires_at <= ?
        ''', (now,))
        expired = c.fetchone()['count']

        # Usuarios únicos con tokens activos
        c.execute('''
            SELECT COUNT(DISTINCT user_id) as count FROM refresh_tokens
            WHERE revoked = 0 AND expires_at > ?
        ''', (now,))
        unique_users = c.fetchone()['count']

        return {
            "total": total,
            "active": active,
            "revoked": revoked,
            "expired": expired,
            "unique_users_with_sessions": unique_users
        }
