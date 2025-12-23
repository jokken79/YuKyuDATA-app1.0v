"""Add full-text search (tsvector) to employee tables.

Revision ID: 003_add_fulltext_search
Revises: 002_initial_schema
Create Date: 2025-12-23 16:00:00.000000

This migration adds full-text search capabilities to the employees, genzai, and ukeoi
tables by:

1. Adding tsvector columns for efficient searching
2. Creating GIN indexes for fast search performance
3. Setting up automatic tsvector updates via generated columns

Full-text search enables:
- Fast employee name searching
- Dispatch location searching
- Status filtering with text search
- Combined field searching (name + location)

Performance:
- GIN indexes: O(log N) search complexity
- Automatic updates: No manual maintenance required
- Supports Japanese text: Using default text search configuration

Rollback:
- Removes tsvector columns and GIN indexes
- Restores original table structure
- No data loss (tsvector is derived from existing columns)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_fulltext_search'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add full-text search columns and indexes."""

    # Add tsvector column to employees table
    # Searches employee name and haken (dispatch location)
    op.add_column(
        'employees',
        sa.Column(
            'search_vector',
            sa.Text,
            sa.Computed(
                "to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(haken, ''))",
                persisted=True
            ),
            nullable=True
        )
    )

    # Create GIN index on employees search_vector
    op.create_index(
        'idx_employees_search',
        'employees',
        ['search_vector'],
        postgresql_using='gin'
    )

    # Add tsvector column to genzai table
    # Searches employee name and dispatch location
    op.add_column(
        'genzai',
        sa.Column(
            'search_vector',
            sa.Text,
            sa.Computed(
                "to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(dispatch_name, '') || ' ' || COALESCE(department, ''))",
                persisted=True
            ),
            nullable=True
        )
    )

    # Create GIN index on genzai search_vector
    op.create_index(
        'idx_genzai_search',
        'genzai',
        ['search_vector'],
        postgresql_using='gin'
    )

    # Add tsvector column to ukeoi table
    # Searches employee name and contract business
    op.add_column(
        'ukeoi',
        sa.Column(
            'search_vector',
            sa.Text,
            sa.Computed(
                "to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(contract_business, ''))",
                persisted=True
            ),
            nullable=True
        )
    )

    # Create GIN index on ukeoi search_vector
    op.create_index(
        'idx_ukeoi_search',
        'ukeoi',
        ['search_vector'],
        postgresql_using='gin'
    )

    # Add tsvector column to staff table
    # Searches employee name and office location
    op.add_column(
        'staff',
        sa.Column(
            'search_vector',
            sa.Text,
            sa.Computed(
                "to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(office, ''))",
                persisted=True
            ),
            nullable=True
        )
    )

    # Create GIN index on staff search_vector
    op.create_index(
        'idx_staff_search',
        'staff',
        ['search_vector'],
        postgresql_using='gin'
    )

    # Analyze tables to update statistics
    op.execute('ANALYZE employees;')
    op.execute('ANALYZE genzai;')
    op.execute('ANALYZE ukeoi;')
    op.execute('ANALYZE staff;')


def downgrade() -> None:
    """Remove full-text search columns and indexes."""

    # Drop indexes
    op.drop_index('idx_employees_search', table_name='employees')
    op.drop_index('idx_genzai_search', table_name='genzai')
    op.drop_index('idx_ukeoi_search', table_name='ukeoi')
    op.drop_index('idx_staff_search', table_name='staff')

    # Drop tsvector columns
    op.drop_column('employees', 'search_vector')
    op.drop_column('genzai', 'search_vector')
    op.drop_column('ukeoi', 'search_vector')
    op.drop_column('staff', 'search_vector')

    # Analyze tables after changes
    op.execute('ANALYZE employees;')
    op.execute('ANALYZE genzai;')
    op.execute('ANALYZE ukeoi;')
    op.execute('ANALYZE staff;')
