"""Create initial PostgreSQL schema for YuKyuDATA

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-12-23 00:00:00.000000

This migration creates all 6 tables for the vacation management system:
- employees: Annual vacation data with balance tracking
- yukyu_usage_details: Granular vacation usage by date
- genzai: Dispatch employee registry
- ukeoi: Contract employee registry
- staff: Direct staff registry
- leave_requests: Vacation request workflow

All tables include strategic indexes for large datasets (>100k rows)
and support for application-level encryption (AES-256-GCM).
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema"""

    # ============================================
    # Table: employees
    # ============================================
    op.create_table(
        'employees',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('employee_num', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('haken', sa.String(255), nullable=True),
        sa.Column('granted', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('used', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('balance', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('expired', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('usage_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('grant_year', sa.Integer(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        postgresql_comment='Annual vacation management (有給休暇管理)'
    )

    op.create_index('idx_emp_num', 'employees', ['employee_num'])
    op.create_index('idx_emp_year', 'employees', ['year'])
    op.create_index('idx_emp_num_year', 'employees', ['employee_num', 'year'])
    op.create_index('idx_emp_haken', 'employees', ['haken'])
    op.create_index('idx_emp_created', 'employees', ['created_at'], postgresql_using='btree')

    # ============================================
    # Table: yukyu_usage_details
    # ============================================
    op.create_table(
        'yukyu_usage_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_num', sa.String(20), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('use_date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('days_used', sa.Numeric(precision=10, scale=2), nullable=True, server_default='1.0'),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_num', 'use_date', name='unique_emp_date'),
        postgresql_comment='Individual vacation usage dates for granular tracking (有給使用詳細)'
    )

    op.create_index('idx_usage_employee_year', 'yukyu_usage_details', ['employee_num', 'year'])
    op.create_index('idx_usage_date', 'yukyu_usage_details', ['use_date'])
    op.create_index('idx_usage_month', 'yukyu_usage_details', ['year', 'month'])

    # ============================================
    # Table: genzai
    # ============================================
    op.create_table(
        'genzai',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('employee_num', sa.String(20), nullable=False),
        sa.Column('dispatch_id', sa.String(50), nullable=True),
        sa.Column('dispatch_name', sa.String(255), nullable=True),
        sa.Column('department', sa.String(255), nullable=True),
        sa.Column('line', sa.String(255), nullable=True),
        sa.Column('job_content', sa.Text(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('kana', sa.String(255), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('nationality', sa.String(50), nullable=True),
        sa.Column('birth_date', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('hourly_wage', sa.Integer(), nullable=True),  # ENCRYPTED
        sa.Column('wage_revision', sa.Text(), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('leave_date', sa.Date(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        postgresql_comment='Dispatch employee registry from DBGenzaiX (派遣社員台帳)'
    )

    op.create_index('idx_genzai_emp', 'genzai', ['employee_num'])
    op.create_index('idx_genzai_status', 'genzai', ['status'])
    op.create_index('idx_genzai_dispatch', 'genzai', ['dispatch_id'])
    op.create_index('idx_genzai_dates', 'genzai', ['hire_date', 'leave_date'])

    # ============================================
    # Table: ukeoi
    # ============================================
    op.create_table(
        'ukeoi',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('employee_num', sa.String(20), nullable=False),
        sa.Column('contract_business', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('kana', sa.String(255), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('nationality', sa.String(50), nullable=True),
        sa.Column('birth_date', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('hourly_wage', sa.Integer(), nullable=True),  # ENCRYPTED
        sa.Column('wage_revision', sa.Text(), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('leave_date', sa.Date(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        postgresql_comment='Contract employee registry from DBUkeoiX (請負社員台帳)'
    )

    op.create_index('idx_ukeoi_emp', 'ukeoi', ['employee_num'])
    op.create_index('idx_ukeoi_status', 'ukeoi', ['status'])
    op.create_index('idx_ukeoi_contract', 'ukeoi', ['contract_business'])
    op.create_index('idx_ukeoi_dates', 'ukeoi', ['hire_date', 'leave_date'])

    # ============================================
    # Table: staff
    # ============================================
    op.create_table(
        'staff',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('employee_num', sa.String(20), nullable=False),
        sa.Column('office', sa.String(255), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('kana', sa.String(255), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('nationality', sa.String(50), nullable=True),
        sa.Column('birth_date', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('visa_expiry', sa.Date(), nullable=True),
        sa.Column('visa_type', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('spouse', sa.String(255), nullable=True),
        sa.Column('postal_code', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('address', sa.Text(), nullable=True),  # ENCRYPTED
        sa.Column('building', sa.String(255), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('leave_date', sa.Date(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        postgresql_comment='Direct staff registry from DBStaffX (社員台帳)'
    )

    op.create_index('idx_staff_emp', 'staff', ['employee_num'])
    op.create_index('idx_staff_status', 'staff', ['status'])
    op.create_index('idx_staff_office', 'staff', ['office'])
    op.create_index('idx_staff_dates', 'staff', ['hire_date', 'leave_date'])
    op.create_index('idx_staff_visa', 'staff', ['visa_expiry'])

    # ============================================
    # Table: leave_requests
    # ============================================
    op.create_table(
        'leave_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_num', sa.String(20), nullable=False),
        sa.Column('employee_name', sa.String(255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('days_requested', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('hours_requested', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('leave_type', sa.String(50), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, server_default='PENDING'),
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('hourly_wage', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('cost_estimate', sa.Numeric(precision=12, scale=2), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        postgresql_comment='Vacation request workflow with approval tracking (休暇申請ワークフロー)'
    )

    op.create_index('idx_lr_emp_num', 'leave_requests', ['employee_num'])
    op.create_index('idx_lr_status', 'leave_requests', ['status'])
    op.create_index('idx_lr_year', 'leave_requests', ['year'])
    op.create_index('idx_lr_dates', 'leave_requests', ['start_date', 'end_date'])
    op.create_index('idx_lr_requested', 'leave_requests', ['requested_at'], postgresql_using='btree')
    op.create_index('idx_lr_emp_year', 'leave_requests', ['employee_num', 'year'])


def downgrade() -> None:
    """Rollback initial schema"""

    op.drop_table('leave_requests')
    op.drop_table('staff')
    op.drop_table('ukeoi')
    op.drop_table('genzai')
    op.drop_table('yukyu_usage_details')
    op.drop_table('employees')
