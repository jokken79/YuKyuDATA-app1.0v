"""Initial UUID schema migration

Revision ID: 001
Revises:
Create Date: 2026-01-17 16:00:00.000000

This migration:
1. Creates all tables with UUID primary keys
2. Maintains backward compatibility with existing data
3. Supports both SQLite and PostgreSQL

Migration Path:
- For SQLite: Direct creation
- For PostgreSQL: Use PostgreSQL-specific UUID type

Note: To migrate from existing SQLite to UUID-based schema:
1. Run database backup
2. Run alembic upgrade head
3. Run migration script to populate UUIDs
4. Verify data integrity
5. Remove old composite key constraints if present
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite
import uuid as uuid_module


# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tables with UUID primary keys."""

    # Detect database type
    conn = op.get_bind()
    db_type = conn.dialect.name

    # Determine UUID column type
    if db_type == 'postgresql':
        uuid_type = postgresql.UUID(as_uuid=True)
    else:
        uuid_type = sa.String(36)

    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('employee_num', sa.String(12), nullable=False, index=True),
        sa.Column('year', sa.Integer, nullable=False, index=True),
        sa.Column('name', sa.String(100)),
        sa.Column('haken', sa.String(100)),
        sa.Column('granted', sa.Float, default=0.0),
        sa.Column('used', sa.Float, default=0.0),
        sa.Column('balance', sa.Float, default=0.0),
        sa.Column('expired', sa.Float, default=0.0),
        sa.Column('usage_rate', sa.Float, default=0.0),
        sa.Column('last_updated', sa.String(50)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('employee_num', 'year', name='uq_emp_year'),
        sa.Index('idx_emp_year', 'employee_num', 'year'),
        sa.Index('idx_emp_created', 'employee_num', 'created_at'),
        sa.Index('idx_year_updated', 'year', 'updated_at'),
    )

    # Create leave_requests table
    op.create_table(
        'leave_requests',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('employee_num', sa.String(12), nullable=False, index=True),
        sa.Column('employee_name', sa.String(100)),
        sa.Column('start_date', sa.String(10), nullable=False),
        sa.Column('end_date', sa.String(10), nullable=False),
        sa.Column('days_requested', sa.Float, nullable=False),
        sa.Column('hours_requested', sa.Integer, default=0),
        sa.Column('leave_type', sa.String(20), default='full'),
        sa.Column('reason', sa.String(500)),
        sa.Column('status', sa.String(20), default='PENDING', index=True),
        sa.Column('year', sa.Integer, nullable=False, index=True),
        sa.Column('hourly_wage', sa.Float),
        sa.Column('approver', sa.String(100)),
        sa.Column('approved_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_emp_status', 'employee_num', 'status'),
        sa.Index('idx_year_status', 'year', 'status'),
        sa.Index('idx_start_end', 'start_date', 'end_date'),
        sa.Index('idx_approved_at', 'approved_at'),
    )

    # Create genzai table (dispatch employees)
    op.create_table(
        'genzai',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('status', sa.String(20)),
        sa.Column('employee_num', sa.String(12), unique=True, index=True),
        sa.Column('dispatch_id', sa.String(50)),
        sa.Column('dispatch_name', sa.String(100)),
        sa.Column('department', sa.String(100)),
        sa.Column('line', sa.String(100)),
        sa.Column('job_content', sa.String(200)),
        sa.Column('name', sa.String(100)),
        sa.Column('kana', sa.String(100)),
        sa.Column('gender', sa.String(10)),
        sa.Column('nationality', sa.String(50)),
        sa.Column('birth_date', sa.String(10)),
        sa.Column('age', sa.Integer),
        sa.Column('hourly_wage', sa.Float),
        sa.Column('wage_revision', sa.String(10)),
        sa.Column('hire_date', sa.String(10)),
        sa.Column('leave_date', sa.String(10)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_genzai_status', 'status'),
        sa.Index('idx_genzai_emp_num', 'employee_num'),
        sa.Index('idx_genzai_dispatch', 'dispatch_id'),
    )

    # Create ukeoi table (contract employees)
    op.create_table(
        'ukeoi',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('status', sa.String(20)),
        sa.Column('employee_num', sa.String(12), unique=True, index=True),
        sa.Column('dispatch_id', sa.String(50)),
        sa.Column('dispatch_name', sa.String(100)),
        sa.Column('department', sa.String(100)),
        sa.Column('line', sa.String(100)),
        sa.Column('job_content', sa.String(200)),
        sa.Column('name', sa.String(100)),
        sa.Column('kana', sa.String(100)),
        sa.Column('gender', sa.String(10)),
        sa.Column('nationality', sa.String(50)),
        sa.Column('birth_date', sa.String(10)),
        sa.Column('age', sa.Integer),
        sa.Column('hourly_wage', sa.Float),
        sa.Column('wage_revision', sa.String(10)),
        sa.Column('hire_date', sa.String(10)),
        sa.Column('leave_date', sa.String(10)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_ukeoi_status', 'status'),
        sa.Index('idx_ukeoi_emp_num', 'employee_num'),
        sa.Index('idx_ukeoi_dispatch', 'dispatch_id'),
    )

    # Create staff table (office staff)
    op.create_table(
        'staff',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('status', sa.String(20)),
        sa.Column('employee_num', sa.String(12), unique=True, index=True),
        sa.Column('dispatch_id', sa.String(50)),
        sa.Column('dispatch_name', sa.String(100)),
        sa.Column('department', sa.String(100)),
        sa.Column('line', sa.String(100)),
        sa.Column('job_content', sa.String(200)),
        sa.Column('name', sa.String(100)),
        sa.Column('kana', sa.String(100)),
        sa.Column('gender', sa.String(10)),
        sa.Column('nationality', sa.String(50)),
        sa.Column('birth_date', sa.String(10)),
        sa.Column('age', sa.Integer),
        sa.Column('hourly_wage', sa.Float),
        sa.Column('wage_revision', sa.String(10)),
        sa.Column('hire_date', sa.String(10)),
        sa.Column('leave_date', sa.String(10)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_staff_status', 'status'),
        sa.Index('idx_staff_emp_num', 'employee_num'),
        sa.Index('idx_staff_dispatch', 'dispatch_id'),
    )

    # Create yukyu_usage_details table
    op.create_table(
        'yukyu_usage_details',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('employee_num', sa.String(12), nullable=False, index=True),
        sa.Column('year', sa.Integer, nullable=False, index=True),
        sa.Column('usage_date', sa.String(10), nullable=False),
        sa.Column('days_used', sa.Float, nullable=False),
        sa.Column('leave_type', sa.String(20), default='full'),
        sa.Column('notes', sa.String(500)),
        sa.Column('source', sa.String(50), default='manual'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_usage_emp_year', 'employee_num', 'year'),
        sa.Index('idx_usage_date', 'usage_date'),
        sa.Index('idx_usage_emp_date', 'employee_num', 'usage_date'),
    )

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('user_id', sa.String(50), nullable=False, index=True),
        sa.Column('notification_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.String(1000)),
        sa.Column('related_id', sa.String(50)),
        sa.Column('related_type', sa.String(50)),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('is_read', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_notif_user', 'user_id'),
        sa.Index('idx_notif_type', 'notification_type'),
        sa.Index('idx_notif_user_type', 'user_id', 'notification_type'),
        sa.Index('idx_notif_created', 'created_at'),
    )

    # Create notification_reads table
    op.create_table(
        'notification_reads',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('user_id', sa.String(50), nullable=False, index=True),
        sa.Column('notification_id', sa.String(36), nullable=False, index=True),
        sa.Column('read_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'notification_id', name='uq_user_notif'),
        sa.Index('idx_notif_read_user', 'user_id'),
        sa.Index('idx_notif_read_notif', 'notification_id'),
        sa.Index('idx_notif_read_at', 'read_at'),
    )

    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('user_id', sa.String(50), index=True),
        sa.Column('action', sa.String(50), nullable=False, index=True),
        sa.Column('table_name', sa.String(50), nullable=False, index=True),
        sa.Column('record_id', sa.String(50), nullable=False, index=True),
        sa.Column('old_values', sa.String(5000)),
        sa.Column('new_values', sa.String(5000)),
        sa.Column('reason', sa.String(500)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_audit_user', 'user_id'),
        sa.Index('idx_audit_action', 'action'),
        sa.Index('idx_audit_table', 'table_name'),
        sa.Index('idx_audit_record', 'record_id'),
        sa.Index('idx_audit_user_action', 'user_id', 'action'),
        sa.Index('idx_audit_created', 'created_at'),
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', uuid_type, primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(100)),
        sa.Column('role', sa.String(20), default='employee'),
        sa.Column('is_active', sa.Integer, default=1),
        sa.Column('last_login', sa.String(19)),
        sa.Column('last_login_ip', sa.String(45)),
        sa.Column('failed_login_attempts', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Index('idx_user_username', 'username'),
        sa.Index('idx_user_email', 'email'),
        sa.Index('idx_user_role', 'role'),
        sa.Index('idx_user_active', 'is_active'),
    )


def downgrade():
    """Drop all tables in reverse order."""
    tables_to_drop = [
        'users',
        'audit_log',
        'notification_reads',
        'notifications',
        'yukyu_usage_details',
        'staff',
        'ukeoi',
        'genzai',
        'leave_requests',
        'employees',
    ]

    for table_name in tables_to_drop:
        try:
            op.drop_table(table_name)
        except:
            # Table might not exist
            pass
