import sqlite3
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_NAME = "yukyu.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections to prevent memory leaks."""
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

        # Indexes for leave_requests table
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_emp_num ON leave_requests(employee_num)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_status ON leave_requests(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_year ON leave_requests(year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_lr_dates ON leave_requests(start_date, end_date)')

        # Indexes for genzai/ukeoi tables
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

        # Add grant_year to employees for FIFO tracking
        try:
            c.execute("ALTER TABLE employees ADD COLUMN grant_year INTEGER")
        except sqlite3.OperationalError:
            pass

        conn.commit()

def save_employees(employees_data):
    """
    Saves a list of employee dictionaries to the database.
    Replaces existing data for the same ID to ensure synchronization.
    """
    with get_db() as conn:
        c = conn.cursor()

        timestamp = datetime.now().isoformat()

        for emp in employees_data:
            # Generate a consistent ID based on employee_num and year if not present
            if 'id' not in emp:
                emp['id'] = f"{emp.get('employeeNum')}_{emp.get('year')}"

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
    """Saves dispatch employee data from DBGenzaiX sheet."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in genzai_data:
            c.execute('''
                INSERT OR REPLACE INTO genzai
                (id, status, employee_num, dispatch_id, dispatch_name, department, line,
                 job_content, name, kana, gender, nationality, birth_date, age,
                 hourly_wage, wage_revision, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
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
                emp.get('birth_date'),
                emp.get('age'),
                emp.get('hourly_wage'),
                emp.get('wage_revision'),
                timestamp
            ))

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
        return [dict(row) for row in rows]

def clear_genzai():
    """Clears genzai table."""
    with get_db() as conn:
        conn.execute("DELETE FROM genzai")
        conn.commit()

# === UKEOI (Contract Employees) Functions ===

def save_ukeoi(ukeoi_data):
    """Saves contract employee data from DBUkeoiX sheet."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in ukeoi_data:
            c.execute('''
                INSERT OR REPLACE INTO ukeoi
                (id, status, employee_num, contract_business, name, kana, gender,
                 nationality, birth_date, age, hourly_wage, wage_revision, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp.get('id'),
                emp.get('status'),
                emp.get('employee_num'),
                emp.get('contract_business'),
                emp.get('name'),
                emp.get('kana'),
                emp.get('gender'),
                emp.get('nationality'),
                emp.get('birth_date'),
                emp.get('age'),
                emp.get('hourly_wage'),
                emp.get('wage_revision'),
                timestamp
            ))

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
        return [dict(row) for row in rows]


# === STAFF Functions ===

def save_staff(staff_data):
    """Saves staff employee data from DBStaffX sheet."""
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        for emp in staff_data:
            c.execute('''
                INSERT OR REPLACE INTO staff
                (id, status, employee_num, office, name, kana, gender, nationality,
                 birth_date, age, visa_expiry, visa_type, spouse, postal_code,
                 address, building, hire_date, leave_date, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp.get('id'),
                emp.get('status'),
                emp.get('employee_num'),
                emp.get('office'),
                emp.get('name'),
                emp.get('kana'),
                emp.get('gender'),
                emp.get('nationality'),
                emp.get('birth_date'),
                emp.get('age'),
                emp.get('visa_expiry'),
                emp.get('visa_type'),
                emp.get('spouse'),
                emp.get('postal_code'),
                emp.get('address'),
                emp.get('building'),
                emp.get('hire_date'),
                emp.get('leave_date'),
                timestamp
            ))

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
        return [dict(row) for row in rows]


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

def create_leave_request(employee_num, employee_name, start_date, end_date, days_requested, reason, year,
                         hours_requested=0, leave_type='full', hourly_wage=0):
    """Creates a new leave request (yukyu solicitud).

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
            c.execute('''
                INSERT OR REPLACE INTO yukyu_usage_details
                (employee_num, name, use_date, year, month, days_used, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                detail.get('employee_num'),
                detail.get('name'),
                detail.get('use_date'),
                detail.get('year'),
                detail.get('month'),
                detail.get('days_used', 1.0),
                timestamp
            ))

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
