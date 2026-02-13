"""Sync schema with current ORM models

Revision ID: 004
Revises: 003
Create Date: 2026-02-06

Changes:
- employees: add grant_date, status, kana, hire_date, after_expiry columns;
  change unique constraint from (employee_num, year) to (employee_num, year, grant_date)
- ukeoi: remove dispatch_id/dispatch_name/department/line/job_content/hire_date/leave_date,
  add contract_business
- staff: remove dispatch_id/dispatch_name/department/line/job_content/hourly_wage/wage_revision,
  add office/visa_expiry/visa_type/spouse/postal_code/address/building/hire_date/leave_date
- yukyu_usage_details: rename usage_date -> use_date, add name/month columns,
  change source default from 'manual' to 'excel'
"""

from alembic import op
import sqlalchemy as sa


revision = '004'
down_revision = '003_add_fulltext_search'
branch_labels = None
depends_on = None


def upgrade():
    # =============================================
    # EMPLOYEES: add missing columns
    # =============================================
    with op.batch_alter_table('employees', schema=None) as batch_op:
        batch_op.add_column(sa.Column('grant_date', sa.String(10)))
        batch_op.add_column(sa.Column('status', sa.String(20)))
        batch_op.add_column(sa.Column('kana', sa.String(100)))
        batch_op.add_column(sa.Column('hire_date', sa.String(10)))
        batch_op.add_column(sa.Column('after_expiry', sa.Float, server_default='0'))
        batch_op.create_index('idx_emp_status', ['status'])
        # Drop old unique constraint and create new one
        try:
            batch_op.drop_constraint('uq_emp_year', type_='unique')
        except Exception:
            pass
        batch_op.create_unique_constraint(
            'uq_emp_year_grant', ['employee_num', 'year', 'grant_date']
        )

    # =============================================
    # UKEOI: restructure columns
    # =============================================
    with op.batch_alter_table('ukeoi', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contract_business', sa.String(200)))
        # Remove old columns
        for col in ['dispatch_id', 'dispatch_name', 'department',
                     'line', 'job_content', 'hire_date', 'leave_date']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
        # Remove old index
        try:
            batch_op.drop_index('idx_ukeoi_dispatch')
        except Exception:
            pass

    # =============================================
    # STAFF: restructure columns
    # =============================================
    with op.batch_alter_table('staff', schema=None) as batch_op:
        batch_op.add_column(sa.Column('office', sa.String(100)))
        batch_op.add_column(sa.Column('visa_expiry', sa.String(10)))
        batch_op.add_column(sa.Column('visa_type', sa.String(50)))
        batch_op.add_column(sa.Column('spouse', sa.String(20)))
        batch_op.add_column(sa.Column('postal_code', sa.String(10)))
        batch_op.add_column(sa.Column('address', sa.String(200)))
        batch_op.add_column(sa.Column('building', sa.String(100)))
        # Remove old columns
        for col in ['dispatch_id', 'dispatch_name', 'department',
                     'line', 'job_content', 'hourly_wage', 'wage_revision']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
        # Remove old index
        try:
            batch_op.drop_index('idx_staff_dispatch')
        except Exception:
            pass

    # =============================================
    # YUKYU_USAGE_DETAILS: rename + add columns
    # =============================================
    with op.batch_alter_table('yukyu_usage_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(100)))
        batch_op.add_column(sa.Column('month', sa.Integer))
        # Rename usage_date -> use_date
        batch_op.alter_column('usage_date', new_column_name='use_date')
        # Update indexes for renamed column
        try:
            batch_op.drop_index('idx_usage_date')
        except Exception:
            pass
        try:
            batch_op.drop_index('idx_usage_emp_date')
        except Exception:
            pass
        batch_op.create_index('idx_usage_date', ['use_date'])
        batch_op.create_index('idx_usage_emp_date', ['employee_num', 'use_date'])


def downgrade():
    """Reverse the schema changes."""
    # EMPLOYEES: remove added columns, restore old constraint
    with op.batch_alter_table('employees', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('uq_emp_year_grant', type_='unique')
        except Exception:
            pass
        batch_op.create_unique_constraint(
            'uq_emp_year', ['employee_num', 'year']
        )
        try:
            batch_op.drop_index('idx_emp_status')
        except Exception:
            pass
        for col in ['grant_date', 'status', 'kana', 'hire_date', 'after_expiry']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass

    # UKEOI: restore old columns
    with op.batch_alter_table('ukeoi', schema=None) as batch_op:
        try:
            batch_op.drop_column('contract_business')
        except Exception:
            pass
        batch_op.add_column(sa.Column('dispatch_id', sa.String(50)))
        batch_op.add_column(sa.Column('dispatch_name', sa.String(100)))
        batch_op.add_column(sa.Column('department', sa.String(100)))
        batch_op.add_column(sa.Column('line', sa.String(100)))
        batch_op.add_column(sa.Column('job_content', sa.String(200)))
        batch_op.add_column(sa.Column('hire_date', sa.String(10)))
        batch_op.add_column(sa.Column('leave_date', sa.String(10)))
        batch_op.create_index('idx_ukeoi_dispatch', ['dispatch_id'])

    # STAFF: restore old columns
    with op.batch_alter_table('staff', schema=None) as batch_op:
        for col in ['office', 'visa_expiry', 'visa_type', 'spouse',
                     'postal_code', 'address', 'building']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
        batch_op.add_column(sa.Column('dispatch_id', sa.String(50)))
        batch_op.add_column(sa.Column('dispatch_name', sa.String(100)))
        batch_op.add_column(sa.Column('department', sa.String(100)))
        batch_op.add_column(sa.Column('line', sa.String(100)))
        batch_op.add_column(sa.Column('job_content', sa.String(200)))
        batch_op.add_column(sa.Column('hourly_wage', sa.Float))
        batch_op.add_column(sa.Column('wage_revision', sa.String(10)))
        batch_op.create_index('idx_staff_dispatch', ['dispatch_id'])

    # YUKYU_USAGE_DETAILS: reverse rename + remove columns
    with op.batch_alter_table('yukyu_usage_details', schema=None) as batch_op:
        try:
            batch_op.drop_index('idx_usage_date')
        except Exception:
            pass
        try:
            batch_op.drop_index('idx_usage_emp_date')
        except Exception:
            pass
        batch_op.alter_column('use_date', new_column_name='usage_date')
        batch_op.create_index('idx_usage_date', ['usage_date'])
        batch_op.create_index('idx_usage_emp_date', ['employee_num', 'usage_date'])
        for col in ['name', 'month']:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
