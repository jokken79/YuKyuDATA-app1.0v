from sqlalchemy import inspect, text
from orm import engine
# Use the Base from orm/models/base.py where all models are actually registered.
# NOTE: orm/__init__.py has a SEPARATE Base instance that only has refresh_tokens.
from orm.models.base import Base
# Import all models to ensure they are registered with Base
from orm.models import (  # noqa: F401
    Employee,
    YukyuUsageDetail,
    GenzaiEmployee,
    UkeoiEmployee,
    StaffEmployee,
    LeaveRequest,
    AuditLog,
    Notification,
    NotificationRead,
    User,
)

import logging
import sqlite3

logger = logging.getLogger(__name__)

# ============================================
# SCHEMA MIGRATION DEFINITIONS
# ============================================
# Defines columns that must exist per table, matching current ORM models.
# Format: (column_name, sql_type_sqlite, sql_type_postgresql, default_value_or_None)
#
# NOTE: SQLite ALTER TABLE ADD COLUMN only allows constant defaults.
# CURRENT_TIMESTAMP is NOT allowed. Use None (NULL default) for datetime columns;
# the ORM BaseModel provides created_at/updated_at defaults in Python code.

_REQUIRED_COLUMNS = {
    'employees': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
        ('grant_date', 'VARCHAR(10)', 'VARCHAR(10)', None),
        ('status', 'VARCHAR(20)', 'VARCHAR(20)', None),
        ('kana', 'VARCHAR(100)', 'VARCHAR(100)', None),
        ('hire_date', 'VARCHAR(10)', 'VARCHAR(10)', None),
        ('after_expiry', 'REAL', 'FLOAT', '0'),
    ],
    'yukyu_usage_details': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
        ('name', 'VARCHAR(100)', 'VARCHAR(100)', None),
        ('month', 'INTEGER', 'INTEGER', None),
        ('leave_type', 'VARCHAR(20)', 'VARCHAR(20)', "'full'"),
        ('notes', 'VARCHAR(500)', 'VARCHAR(500)', None),
        ('source', 'VARCHAR(50)', 'VARCHAR(50)', "'excel'"),
    ],
    'genzai': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
    ],
    'ukeoi': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
        ('contract_business', 'VARCHAR(200)', 'VARCHAR(200)', None),
    ],
    'staff': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
        ('office', 'VARCHAR(100)', 'VARCHAR(100)', None),
        ('visa_expiry', 'VARCHAR(10)', 'VARCHAR(10)', None),
        ('visa_type', 'VARCHAR(50)', 'VARCHAR(50)', None),
        ('spouse', 'VARCHAR(20)', 'VARCHAR(20)', None),
        ('postal_code', 'VARCHAR(10)', 'VARCHAR(10)', None),
        ('address', 'VARCHAR(200)', 'VARCHAR(200)', None),
        ('building', 'VARCHAR(100)', 'VARCHAR(100)', None),
    ],
    'leave_requests': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
    ],
    'audit_log': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
    ],
    'notification_reads': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
    ],
    'notifications': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
    ],
    'users': [
        ('created_at', 'DATETIME', 'TIMESTAMP', None),
        ('updated_at', 'DATETIME', 'TIMESTAMP', None),
    ],
}

# Unique constraints to create if missing
_REQUIRED_UNIQUE_CONSTRAINTS = {
    'employees': [
        ('uq_emp_year_grant', ['employee_num', 'year', 'grant_date']),
    ],
    'genzai': [
        ('uq_genzai_employee_num', ['employee_num']),
    ],
    'ukeoi': [
        ('uq_ukeoi_employee_num', ['employee_num']),
    ],
    'staff': [
        ('uq_staff_employee_num', ['employee_num']),
    ],
}


def _get_sqlite_db_path() -> str:
    """Extract the file path from the SQLite engine URL."""
    url = str(engine.url)
    # sqlite:///yukyu.db -> yukyu.db
    # sqlite:////absolute/path.db -> /absolute/path.db
    if url.startswith('sqlite:///'):
        return url[len('sqlite:///'):]
    return 'yukyu.db'


def _fix_integer_id_tables_sqlite(db_path: str):
    """
    Fix tables that have INTEGER id but ORM expects TEXT (UUID).

    SQLite cannot ALTER COLUMN types, so we must drop and recreate.
    Data in these tables is re-importable from Excel (usage details)
    or is operational data (leave requests, audit logs) that we preserve
    by converting the integer id to a text string.

    Uses raw sqlite3 to avoid SQLAlchemy inspector caching issues.
    """
    from sqlalchemy import String as SAString

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        # Get all tables
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]

        for table_name in tables:
            # Get column info
            cursor = conn.execute(f"PRAGMA table_info('{table_name}')")
            columns = cursor.fetchall()
            id_col = next((c for c in columns if c['name'] == 'id'), None)

            if not id_col or id_col['type'] != 'INTEGER':
                continue

            # Check if ORM model expects String/TEXT for this table
            orm_table = Base.metadata.tables.get(table_name)
            if orm_table is None:
                continue
            orm_id_col = orm_table.columns.get('id')
            if orm_id_col is None or not isinstance(orm_id_col.type, SAString):
                continue

            # This table needs migration: INTEGER id -> TEXT id
            logger.info(f"Schema migration: {table_name} needs id type change (INTEGER -> TEXT)")

            old_name = f"_migrate_old_{table_name}"

            try:
                # 1. Rename old table
                conn.execute(f"ALTER TABLE [{table_name}] RENAME TO [{old_name}]")
                logger.info(f"Schema migration: renamed [{table_name}] -> [{old_name}]")
            except Exception as e:
                logger.warning(f"Schema migration: rename failed for {table_name}: {e}")
                continue

        conn.commit()
    finally:
        conn.close()


def _cleanup_old_migrate_tables_sqlite(db_path: str):
    """Drop leftover _migrate_old_ tables after create_all has recreated them."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '_migrate_old_%'")
        old_tables = [row[0] for row in cursor.fetchall()]

        for old_table in old_tables:
            try:
                conn.execute(f"DROP TABLE IF EXISTS [{old_table}]")
                logger.info(f"Schema migration: dropped leftover [{old_table}]")
            except Exception as e:
                logger.warning(f"Schema migration: could not drop [{old_table}]: {e}")

        conn.commit()
    finally:
        conn.close()


def init_db():
    """
    Initialize database using SQLAlchemy ORM.
    Also performs schema migration for existing tables to match ORM models.

    Handles three types of schema drift:
    1. Wrong id column type (INTEGER vs TEXT/UUID) -- drops and recreates table
    2. Missing columns (added via ALTER TABLE ADD COLUMN)
    3. Missing unique constraints (created via CREATE UNIQUE INDEX)

    SQLAlchemy create_all() only creates NEW tables, not modify existing ones.
    """
    is_sqlite = 'sqlite' in str(engine.url)

    if is_sqlite:
        db_path = _get_sqlite_db_path()

        # Phase 0: Rename tables with INTEGER id to _migrate_old_
        # This MUST happen before create_all() using raw sqlite3
        # (avoids SQLAlchemy inspector caching issues)
        _fix_integer_id_tables_sqlite(db_path)

    # Create all tables defined in ORM models.
    # Creates NEW tables (including those just renamed away in phase 0).
    Base.metadata.create_all(bind=engine)

    if is_sqlite:
        # Drop the renamed old tables (data was in legacy format anyway)
        _cleanup_old_migrate_tables_sqlite(db_path)

    # Phase 1: Add missing columns to existing tables
    # Need a fresh inspector after create_all
    insp = inspect(engine)
    # Clear inspector cache to pick up newly created tables
    insp.clear_cache()

    with engine.connect() as conn:
        tables = insp.get_table_names()

        for table, required_cols in _REQUIRED_COLUMNS.items():
            if table not in tables:
                continue

            existing_columns = {c['name'] for c in insp.get_columns(table)}

            for col_name, sqlite_type, pg_type, default_val in required_cols:
                if col_name in existing_columns:
                    continue

                col_type = sqlite_type if is_sqlite else pg_type
                default_clause = f" DEFAULT {default_val}" if default_val else ""
                sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}{default_clause}"

                try:
                    conn.execute(text(sql))
                    logger.info(f"Schema migration: {table}.{col_name} ({col_type}) added")
                except Exception as e:
                    logger.warning(f"Schema migration skipped {table}.{col_name}: {e}")

        # Phase 2: Create unique constraints if missing (SQLite only via index)
        if is_sqlite:
            for table, constraints in _REQUIRED_UNIQUE_CONSTRAINTS.items():
                if table not in tables:
                    continue
                existing_indexes = {idx['name'] for idx in insp.get_indexes(table) if idx.get('name')}
                for constraint_name, columns in constraints:
                    if constraint_name not in existing_indexes:
                        cols_str = ', '.join(columns)
                        sql = f"CREATE UNIQUE INDEX IF NOT EXISTS {constraint_name} ON {table} ({cols_str})"
                        try:
                            conn.execute(text(sql))
                            logger.info(f"Schema migration: created unique index {constraint_name} on {table}")
                        except Exception as e:
                            logger.warning(f"Schema migration skipped index {constraint_name}: {e}")

        conn.commit()
