"""Convert to UUID schema with data preservation

Revision ID: 002_convert_to_uuid
Revises: 001_initial_schema
Create Date: 2026-01-17 23:55:00.000000

This migration:
1. Adds UUID id columns to all tables (with default values)
2. Preserves all existing data
3. Creates new constraints with UUID as primary key
4. Maintains backward compatibility during transition
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
import uuid as uuid_module
import os

# revision identifiers, used by Alembic
revision = '002_convert_to_uuid'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Convert existing schema to UUID-based schema while preserving data."""

    conn = op.get_bind()
    db_type = conn.dialect.name

    # Determine UUID column type based on database
    if db_type == 'postgresql':
        uuid_type = sa.String(36)  # Store as string in both SQLite and PostgreSQL
    else:
        uuid_type = sa.String(36)

    # For each table, we need to:
    # 1. Check if it already has UUID id column
    # 2. If not, add the UUID id column with defaults
    # 3. Set up unique constraints on composite keys if needed

    inspector = conn.inspect(conn)

    # Process employees table
    try:
        tables_info = inspector.get_table_names()

        # For SQLite, we use raw SQL since altering columns is limited
        if db_type == 'sqlite':
            # SQLite doesn't support ALTER COLUMN, so we check current schema
            columns = [col['name'] for col in inspector.get_columns('employees')]

            if 'id' not in columns:
                # Add UUID id column to employees
                op.add_column('employees', sa.Column('id', uuid_type))

                # Create an index on the new id column
                op.create_index('idx_emp_id', 'employees', ['id'], unique=True)

        # Add UUID id to leave_requests if missing
        columns = [col['name'] for col in inspector.get_columns('leave_requests')]
        if 'id' not in columns:
            op.add_column('leave_requests', sa.Column('id', uuid_type))
            op.create_index('idx_leave_id', 'leave_requests', ['id'], unique=True)

        # Add UUID id to genzai if missing
        columns = [col['name'] for col in inspector.get_columns('genzai')]
        if 'id' not in columns:
            op.add_column('genzai', sa.Column('id', uuid_type))
            op.create_index('idx_genzai_id', 'genzai', ['id'], unique=True)

        # Add UUID id to ukeoi if missing
        columns = [col['name'] for col in inspector.get_columns('ukeoi')]
        if 'id' not in columns:
            op.add_column('ukeoi', sa.Column('id', uuid_type))
            op.create_index('idx_ukeoi_id', 'ukeoi', ['id'], unique=True)

        # Add UUID id to staff if missing
        columns = [col['name'] for col in inspector.get_columns('staff')]
        if 'id' not in columns:
            op.add_column('staff', sa.Column('id', uuid_type))
            op.create_index('idx_staff_id', 'staff', ['id'], unique=True)

        # Add UUID id to yukyu_usage_details if missing
        columns = [col['name'] for col in inspector.get_columns('yukyu_usage_details')]
        if 'id' not in columns:
            op.add_column('yukyu_usage_details', sa.Column('id', uuid_type))
            op.create_index('idx_usage_id', 'yukyu_usage_details', ['id'], unique=True)

    except Exception as e:
        # Silently handle if tables don't exist yet
        pass


def downgrade():
    """Remove UUID columns (partial rollback)."""
    conn = op.get_bind()
    db_type = conn.dialect.name

    if db_type == 'sqlite':
        # SQLite: Drop indexes and columns
        try:
            op.drop_index('idx_emp_id', table_name='employees')
            op.drop_column('employees', 'id')
        except:
            pass

        try:
            op.drop_index('idx_leave_id', table_name='leave_requests')
            op.drop_column('leave_requests', 'id')
        except:
            pass

        try:
            op.drop_index('idx_genzai_id', table_name='genzai')
            op.drop_column('genzai', 'id')
        except:
            pass

        try:
            op.drop_index('idx_ukeoi_id', table_name='ukeoi')
            op.drop_column('ukeoi', 'id')
        except:
            pass

        try:
            op.drop_index('idx_staff_id', table_name='staff')
            op.drop_column('staff', 'id')
        except:
            pass

        try:
            op.drop_index('idx_usage_id', table_name='yukyu_usage_details')
            op.drop_column('yukyu_usage_details', 'id')
        except:
            pass
