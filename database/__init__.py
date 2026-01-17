"""
YuKyuDATA Database Layer - Modularized
Centralizes database operations with separation of concerns

Structure:
- connection.py: Database connections (SQLite/PostgreSQL)
- crud.py: CRUD operations for all entity types
- validation.py: Business rule validations
- backups.py: Backup and restore operations
- audit.py: Audit logging and history tracking
- notifications.py: Notification read status tracking
- leave_requests.py: Leave request workflow
- yukyu_usage.py: Yukyu (paid leave) usage tracking
- bulk_operations.py: Batch processing operations
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator, Dict, List, Any

# Import the connection manager
from database.connection import ConnectionManager, get_db_path, USE_POSTGRESQL, DB_NAME, DATABASE_URL, db_manager

# Module exports
__all__ = [
    # Connection
    'get_db', 'get_db_connection', 'get_db_path', 'init_db',
    'USE_POSTGRESQL', 'DB_NAME', 'DATABASE_URL',

    # CRUD
    'save_employees', 'get_employees', 'get_available_years', 'get_employees_enhanced',
    'clear_database', 'save_genzai', 'get_genzai', 'clear_genzai',
    'save_ukeoi', 'get_ukeoi', 'clear_ukeoi',
    'save_staff', 'get_staff', 'clear_staff',
    'get_stats_by_factory', 'update_employee', 'get_employee_usage_summary',

    # Validation
    'validate_balance_limit', 'get_employee_total_balance',

    # Leave Requests
    'create_leave_request', 'get_leave_requests', 'approve_leave_request',
    'reject_leave_request', 'cancel_leave_request', 'revert_approved_request',

    # Yukyu Usage
    'get_employee_yukyu_history', 'delete_old_yukyu_records',
    'save_yukyu_usage_details', 'get_yukyu_usage_details', 'get_monthly_usage_summary',
    'update_yukyu_usage_detail', 'delete_yukyu_usage_detail',
    'add_single_yukyu_usage', 'recalculate_employee_used_days',

    # Backups
    'create_backup', 'list_backups', 'restore_backup',

    # Audit
    'log_audit', 'get_audit_log', 'get_audit_log_by_user',
    'get_entity_history', 'get_audit_stats', 'cleanup_old_audit_logs',

    # Bulk Operations
    'init_bulk_audit_table', 'bulk_update_employees',
    'get_bulk_update_history', 'revert_bulk_update',

    # Notifications
    'mark_notification_read', 'mark_all_notifications_read',
    'is_notification_read', 'get_read_notification_ids', 'get_unread_count',
]

logger = logging.getLogger(__name__)

# ============================================================================
# CONNECTION MANAGEMENT
# ============================================================================

def _get_param_placeholder() -> str:
    """Get parameter placeholder for current database."""
    return '%s' if USE_POSTGRESQL else '?'


def _convert_query_placeholders(query: str) -> str:
    """Convert SQLite ? placeholders to PostgreSQL %s if needed."""
    if not USE_POSTGRESQL:
        return query
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
        with db_manager.get_connection() as conn:
            yield conn
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database schema - create all tables if they don't exist."""
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

        # Create indices
        c.execute('CREATE INDEX IF NOT EXISTS idx_emp_year ON employees(year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_emp_num ON employees(employee_num)')

        # Genzai table
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
                hourly_wage REAL,
                wage_revision TEXT,
                hire_date TEXT,
                leave_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_status ON genzai(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_genzai_emp ON genzai(employee_num)')

        # Ukeoi table
        c.execute('''
            CREATE TABLE IF NOT EXISTS ukeoi (
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
                hourly_wage REAL,
                wage_revision TEXT,
                hire_date TEXT,
                leave_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ukeoi_status ON ukeoi(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_ukeoi_emp ON ukeoi(employee_num)')

        # Staff table
        c.execute('''
            CREATE TABLE IF NOT EXISTS staff (
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
                hourly_wage REAL,
                wage_revision TEXT,
                hire_date TEXT,
                leave_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_staff_status ON staff(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_staff_emp ON staff(employee_num)')

        # Leave requests table
        c.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT,
                employee_name TEXT,
                start_date TEXT,
                end_date TEXT,
                days_requested REAL,
                hours_requested INTEGER DEFAULT 0,
                leave_type TEXT DEFAULT 'full',
                reason TEXT,
                status TEXT DEFAULT 'PENDING',
                year INTEGER,
                hourly_wage REAL,
                approver TEXT,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_leave_status ON leave_requests(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_leave_year ON leave_requests(year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_leave_emp ON leave_requests(employee_num)')

        # Yukyu usage details table
        c.execute('''
            CREATE TABLE IF NOT EXISTS yukyu_usage_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_num TEXT NOT NULL,
                use_date TEXT NOT NULL,
                days_used REAL NOT NULL,
                month INTEGER,
                year INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_usage_emp_year ON yukyu_usage_details(employee_num, year)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_usage_year ON yukyu_usage_details(year)')

        # Audit log table
        c.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                action TEXT,
                entity_type TEXT,
                entity_id TEXT,
                old_value TEXT,
                new_value TEXT,
                details TEXT,
                ip_address TEXT
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id)')

        # Bulk update history table
        c.execute('''
            CREATE TABLE IF NOT EXISTS bulk_update_history (
                id TEXT PRIMARY KEY,
                operation_id TEXT UNIQUE,
                employee_num TEXT,
                year INTEGER,
                field_name TEXT,
                old_value TEXT,
                new_value TEXT,
                updated_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bulk_op ON bulk_update_history(operation_id)')

        # Notification reads table
        c.execute('''
            CREATE TABLE IF NOT EXISTS notification_reads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(notification_id, user_id)
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_notif_user ON notification_reads(user_id)')

        conn.commit()
        logger.info("Database initialized successfully")


# ============================================================================
# LAZY IMPORTS - Load specific modules only when needed
# ============================================================================

def _import_crud_functions():
    """Lazy import CRUD functions"""
    global save_employees, get_employees, get_available_years, get_employees_enhanced
    global clear_database, save_genzai, get_genzai, clear_genzai
    global save_ukeoi, get_ukeoi, clear_ukeoi
    global save_staff, get_staff, clear_staff, get_stats_by_factory
    global update_employee, get_employee_usage_summary

    from database.crud import (
        save_employees, get_employees, get_available_years, get_employees_enhanced,
        clear_database, save_genzai, get_genzai, clear_genzai,
        save_ukeoi, get_ukeoi, clear_ukeoi,
        save_staff, get_staff, clear_staff, get_stats_by_factory,
        update_employee, get_employee_usage_summary
    )


def _import_validation_functions():
    """Lazy import validation functions"""
    global validate_balance_limit, get_employee_total_balance

    from database.validation import (
        validate_balance_limit, get_employee_total_balance
    )


def _import_leave_functions():
    """Lazy import leave request functions"""
    global create_leave_request, get_leave_requests, approve_leave_request
    global reject_leave_request, cancel_leave_request, revert_approved_request

    from database.leave_requests import (
        create_leave_request, get_leave_requests, approve_leave_request,
        reject_leave_request, cancel_leave_request, revert_approved_request
    )


def _import_yukyu_functions():
    """Lazy import yukyu usage functions"""
    global get_employee_yukyu_history, delete_old_yukyu_records
    global save_yukyu_usage_details, get_yukyu_usage_details, get_monthly_usage_summary
    global update_yukyu_usage_detail, delete_yukyu_usage_detail
    global add_single_yukyu_usage, recalculate_employee_used_days

    from database.yukyu_usage import (
        get_employee_yukyu_history, delete_old_yukyu_records,
        save_yukyu_usage_details, get_yukyu_usage_details, get_monthly_usage_summary,
        update_yukyu_usage_detail, delete_yukyu_usage_detail,
        add_single_yukyu_usage, recalculate_employee_used_days
    )


def _import_backup_functions():
    """Lazy import backup functions"""
    global create_backup, list_backups, restore_backup

    from database.backups import (
        create_backup, list_backups, restore_backup
    )


def _import_audit_functions():
    """Lazy import audit functions"""
    global log_audit, get_audit_log, get_audit_log_by_user
    global get_entity_history, get_audit_stats, cleanup_old_audit_logs

    from database.audit import (
        log_audit, get_audit_log, get_audit_log_by_user,
        get_entity_history, get_audit_stats, cleanup_old_audit_logs
    )


def _import_bulk_functions():
    """Lazy import bulk operation functions"""
    global init_bulk_audit_table, bulk_update_employees
    global get_bulk_update_history, revert_bulk_update

    from database.bulk_operations import (
        init_bulk_audit_table, bulk_update_employees,
        get_bulk_update_history, revert_bulk_update
    )


def _import_notification_functions():
    """Lazy import notification functions"""
    global mark_notification_read, mark_all_notifications_read
    global is_notification_read, get_read_notification_ids, get_unread_count

    from database.notifications import (
        mark_notification_read, mark_all_notifications_read,
        is_notification_read, get_read_notification_ids, get_unread_count
    )


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Import lazy loader
def __getattr__(name):
    """Lazy load module functions on demand"""
    if name in ('save_employees', 'get_employees', 'clear_database'):
        _import_crud_functions()
        return globals()[name]
    elif name in ('validate_balance_limit', 'get_employee_total_balance'):
        _import_validation_functions()
        return globals()[name]
    elif name == 'create_leave_request':
        _import_leave_functions()
        return globals()[name]
    elif name == 'create_backup':
        _import_backup_functions()
        return globals()[name]
    elif name == 'log_audit':
        _import_audit_functions()
        return globals()[name]
    elif name == 'bulk_update_employees':
        _import_bulk_functions()
        return globals()[name]
    elif name == 'mark_notification_read':
        _import_notification_functions()
        return globals()[name]

    raise AttributeError(f"module 'database' has no attribute '{name}'")


# Pre-load critical functions for initialization
_import_crud_functions()
_import_validation_functions()
_import_leave_functions()
_import_yukyu_functions()
_import_backup_functions()
_import_audit_functions()
_import_bulk_functions()
_import_notification_functions()

logger.info("Database module initialized successfully")
