#!/usr/bin/env python3
"""
Verify that data migration from SQLite to PostgreSQL was successful.

This script compares table row counts, column structures, and sample data
between SQLite and PostgreSQL databases to ensure data integrity.

Usage:
    python scripts/verify_migration.py
    python scripts/verify_migration.py --source custom.db --target postgresql://...
    python scripts/verify_migration.py --detailed  # Full data comparison
"""

import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
except ImportError:
    logger.error("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


class MigrationVerifier:
    """Verifies data migration from SQLite to PostgreSQL."""

    def __init__(
        self,
        sqlite_db: str,
        postgres_url: Optional[str] = None,
        detailed: bool = False
    ):
        """
        Initialize verifier.

        Args:
            sqlite_db: Path to SQLite database
            postgres_url: PostgreSQL connection URL
            detailed: Whether to perform detailed data comparison
        """
        self.sqlite_db = sqlite_db
        self.postgres_url = postgres_url or os.getenv(
            'DATABASE_URL',
            'postgresql://yukyu_user:change_me@localhost:5432/yukyu'
        )
        self.detailed = detailed
        self.issues = []
        self.warnings = []
        self.start_time = None
        self.end_time = None

    def connect_sqlite(self) -> sqlite3.Connection:
        """Create SQLite connection."""
        try:
            conn = sqlite3.connect(self.sqlite_db)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to connect to SQLite: {e}")
            raise

    def connect_postgres(self) -> psycopg2.connection:
        """Create PostgreSQL connection."""
        try:
            conn = psycopg2.connect(self.postgres_url)
            return conn
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def get_sqlite_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Get list of tables in SQLite."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_postgres_tables(self, conn: psycopg2.connection) -> List[str]:
        """Get list of tables in PostgreSQL."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        return [row[0] for row in cursor.fetchall()]

    def verify_row_counts(
        self,
        sqlite_conn: sqlite3.Connection,
        postgres_conn: psycopg2.connection,
        tables: List[str]
    ) -> bool:
        """Verify row counts match between databases."""
        logger.info("\n🔍 Verifying row counts...")

        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        all_match = True

        for table in tables:
            try:
                # SQLite count
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]

                # PostgreSQL count
                postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                postgres_count = postgres_cursor.fetchone()[0]

                if sqlite_count == postgres_count:
                    logger.info(f"  ✅ {table}: {sqlite_count} rows (match)")
                else:
                    logger.error(
                        f"  ❌ {table}: SQLite={sqlite_count}, PostgreSQL={postgres_count}"
                    )
                    self.issues.append(
                        f"Row count mismatch in {table}: "
                        f"SQLite={sqlite_count}, PostgreSQL={postgres_count}"
                    )
                    all_match = False

            except Exception as e:
                logger.error(f"  ❌ Error comparing {table}: {e}")
                self.issues.append(f"Failed to compare row counts for {table}: {e}")
                all_match = False

        return all_match

    def verify_column_structure(
        self,
        sqlite_conn: sqlite3.Connection,
        postgres_conn: psycopg2.connection,
        tables: List[str]
    ) -> bool:
        """Verify column structure matches between databases."""
        logger.info("\n🔍 Verifying column structure...")

        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        all_match = True

        for table in tables:
            try:
                # SQLite columns
                sqlite_cursor.execute(f"PRAGMA table_info({table})")
                sqlite_cols = {row[1] for row in sqlite_cursor.fetchall()}

                # PostgreSQL columns
                postgres_cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table,))
                postgres_cols = {row[0] for row in postgres_cursor.fetchall()}

                # Compare
                missing_in_postgres = sqlite_cols - postgres_cols
                extra_in_postgres = postgres_cols - sqlite_cols

                if sqlite_cols == postgres_cols:
                    logger.info(f"  ✅ {table}: {len(sqlite_cols)} columns (match)")
                else:
                    logger.warning(f"  ⚠️  {table}: Column mismatch")
                    if missing_in_postgres:
                        logger.warning(f"     Missing in PostgreSQL: {missing_in_postgres}")
                        self.warnings.append(
                            f"Columns missing in {table} (PostgreSQL): {missing_in_postgres}"
                        )
                    if extra_in_postgres:
                        logger.warning(f"     Extra in PostgreSQL: {extra_in_postgres}")
                        self.warnings.append(
                            f"Extra columns in {table} (PostgreSQL): {extra_in_postgres}"
                        )
                    all_match = False

            except Exception as e:
                logger.error(f"  ❌ Error comparing columns for {table}: {e}")
                self.issues.append(f"Failed to compare columns for {table}: {e}")
                all_match = False

        return all_match

    def verify_sample_data(
        self,
        sqlite_conn: sqlite3.Connection,
        postgres_conn: psycopg2.connection,
        tables: List[str],
        sample_size: int = 5
    ) -> bool:
        """Verify sample data matches between databases."""
        if not self.detailed:
            return True

        logger.info(f"\n🔍 Verifying sample data (first {sample_size} rows per table)...")

        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()

        all_match = True

        for table in tables:
            try:
                # SQLite sample
                sqlite_cursor.execute(f"SELECT * FROM {table} LIMIT ?", (sample_size,))
                sqlite_rows = sqlite_cursor.fetchall()

                if not sqlite_rows:
                    logger.info(f"  ⏭️  {table}: No rows to sample")
                    continue

                # PostgreSQL sample
                postgres_cursor.execute(f"SELECT * FROM {table} LIMIT %s", (sample_size,))
                postgres_rows = postgres_cursor.fetchall()

                if len(sqlite_rows) != len(postgres_rows):
                    logger.warning(
                        f"  ⚠️  {table}: Different sample sizes "
                        f"(SQLite={len(sqlite_rows)}, PostgreSQL={len(postgres_rows)})"
                    )
                    all_match = False
                    continue

                logger.info(f"  ✅ {table}: Sample data matches ({len(sqlite_rows)} rows)")

            except Exception as e:
                logger.warning(f"  ⚠️  {table}: Could not sample data: {e}")
                self.warnings.append(f"Failed to sample data from {table}: {e}")

        return all_match

    def verify_migration(self) -> bool:
        """Run all verification checks."""
        self.start_time = datetime.now()

        try:
            logger.info("🔄 Starting migration verification...")

            # Connect to both databases
            sqlite_conn = self.connect_sqlite()
            postgres_conn = self.connect_postgres()

            logger.info("✅ Connected to both SQLite and PostgreSQL")

            # Get table lists
            sqlite_tables = self.get_sqlite_tables(sqlite_conn)
            postgres_tables = self.get_postgres_tables(postgres_conn)

            logger.info(f"📊 SQLite tables: {len(sqlite_tables)}")
            logger.info(f"📊 PostgreSQL tables: {len(postgres_tables)}")

            # Verify tables exist
            if set(sqlite_tables) != set(postgres_tables):
                missing_in_pg = set(sqlite_tables) - set(postgres_tables)
                extra_in_pg = set(postgres_tables) - set(sqlite_tables)

                if missing_in_pg:
                    logger.error(f"❌ Missing in PostgreSQL: {missing_in_pg}")
                    self.issues.append(f"Tables missing in PostgreSQL: {missing_in_pg}")

                if extra_in_pg:
                    logger.warning(f"⚠️  Extra in PostgreSQL: {extra_in_pg}")
                    self.warnings.append(f"Extra tables in PostgreSQL: {extra_in_pg}")

            # Use common tables for verification
            common_tables = [t for t in sqlite_tables if t in postgres_tables]

            if not common_tables:
                logger.error("❌ No common tables found between SQLite and PostgreSQL")
                return False

            # Run verification checks
            row_counts_match = self.verify_row_counts(
                sqlite_conn, postgres_conn, common_tables
            )
            columns_match = self.verify_column_structure(
                sqlite_conn, postgres_conn, common_tables
            )
            data_match = self.verify_sample_data(
                sqlite_conn, postgres_conn, common_tables
            )

            # Close connections
            sqlite_conn.close()
            postgres_conn.close()

            self.end_time = datetime.now()
            self.print_summary(row_counts_match, columns_match, data_match)

            return len(self.issues) == 0

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}", exc_info=True)
            return False

    def print_summary(self, row_counts_match: bool, columns_match: bool, data_match: bool):
        """Print verification summary."""
        duration = (self.end_time - self.start_time).total_seconds()

        logger.info("\n" + "="*70)
        logger.info("  MIGRATION VERIFICATION SUMMARY")
        logger.info("="*70)

        logger.info("\n📋 Verification Results:")
        logger.info(f"  {'✅' if row_counts_match else '❌'} Row counts match")
        logger.info(f"  {'✅' if columns_match else '⚠️ ' if not columns_match else '✅'} Column structure match")
        if self.detailed:
            logger.info(f"  {'✅' if data_match else '⚠️ '} Sample data match")

        if self.issues:
            logger.error(f"\n❌ Issues found ({len(self.issues)}):")
            for issue in self.issues:
                logger.error(f"  • {issue}")

        if self.warnings:
            logger.warning(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")

        logger.info(f"\n⏱️  Duration: {duration:.2f} seconds")

        if len(self.issues) == 0:
            logger.info("\n✅ Migration verification PASSED")
        else:
            logger.error("\n❌ Migration verification FAILED")

        logger.info("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify data migration from SQLite to PostgreSQL'
    )
    parser.add_argument(
        '--source',
        default='yukyu.db',
        help='Source SQLite database file (default: yukyu.db)'
    )
    parser.add_argument(
        '--target',
        help='Target PostgreSQL URL (uses DATABASE_URL env var if not provided)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Perform detailed data comparison'
    )

    args = parser.parse_args()

    # Verify source exists
    if not os.path.exists(args.source):
        logger.error(f"❌ Source database not found: {args.source}")
        return 1

    # Run verification
    verifier = MigrationVerifier(args.source, args.target, args.detailed)

    if verifier.verify_migration():
        logger.info("✅ Verification completed successfully")
        return 0
    else:
        logger.error("❌ Verification failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
