#!/usr/bin/env python3
"""
Load JSON data exported from SQLite into PostgreSQL.

This script restores data from a JSON dump file created by dump_sqlite_to_json.py
into a PostgreSQL database, with proper handling of data types and constraints.

Usage:
    python scripts/load_json_to_postgresql.py --source data_export.json
    python scripts/load_json_to_postgresql.py --source data_export.json --verify
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
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
    from psycopg2.extras import execute_values
except ImportError:
    logger.error("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


class PostgreSQLLoader:
    """Loads JSON data into PostgreSQL database."""

    def __init__(self, json_file: str, database_url: Optional[str] = None):
        """
        Initialize loader.

        Args:
            json_file: Path to JSON export file
            database_url: PostgreSQL connection URL (uses env var if not provided)
        """
        self.json_file = json_file
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://yukyu_user:change_me@localhost:5432/yukyu'
        )
        self.data = {}
        self.loaded_counts = {}
        self.start_time = None
        self.end_time = None

    def load_json(self) -> bool:
        """Load JSON file."""
        try:
            logger.info(f"📖 Loading JSON from: {self.json_file}")

            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            logger.info(f"✅ JSON loaded: {self.data.get('total_tables', 0)} tables, "
                       f"{self.data.get('total_rows', 0)} rows")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to load JSON: {e}")
            return False

    def connect(self) -> psycopg2.connection:
        """Create PostgreSQL connection."""
        try:
            conn = psycopg2.connect(self.database_url)
            logger.info("✅ Connected to PostgreSQL")
            return conn
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def get_insert_statement(self, table: str, columns: List[str]) -> str:
        """Generate INSERT statement for table."""
        placeholders = ','.join(['%s'] * len(columns))
        cols = ','.join(columns)
        return f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

    def load_table(self, conn: psycopg2.connection, table: str, rows: List[Dict]) -> int:
        """Load a single table into PostgreSQL."""
        if not rows:
            logger.info(f"  ⏭️  {table}: No rows to load")
            return 0

        try:
            cursor = conn.cursor()
            columns = list(rows[0].keys())

            # Convert rows to tuples
            values = [tuple(row.get(col) for col in columns) for row in rows]

            # Generate INSERT statement
            stmt = self.get_insert_statement(table, columns)

            # Execute bulk insert
            execute_values(cursor, stmt, values, page_size=1000)

            inserted = len(values)
            self.loaded_counts[table] = inserted
            logger.info(f"  ✅ {table}: {inserted} rows loaded")

            return inserted

        except psycopg2.Error as e:
            logger.error(f"  ❌ Failed to load {table}: {e}")
            raise

    def load_all(self, verify: bool = False) -> bool:
        """Load all tables from JSON into PostgreSQL."""
        self.start_time = datetime.now()

        try:
            # Load JSON
            if not self.load_json():
                return False

            # Connect to PostgreSQL
            conn = self.connect()

            # Get tables from JSON
            tables = self.data.get('tables', {})
            json_row_counts = self.data.get('row_counts', {})

            if not tables:
                logger.error("❌ No tables found in JSON file")
                conn.close()
                return False

            logger.info(f"🔄 Loading {len(tables)} tables into PostgreSQL...")

            total_loaded = 0
            for table, rows in tables.items():
                if not rows:
                    logger.info(f"  ⏭️  {table}: No rows")
                    continue

                loaded = self.load_table(conn, table, rows)
                total_loaded += loaded

            # Commit transaction
            conn.commit()
            logger.info(f"✅ All tables committed to PostgreSQL")

            # Verify if requested
            if verify:
                self.verify_load(conn, json_row_counts)

            conn.close()
            self.end_time = datetime.now()
            self.print_summary()

            return True

        except Exception as e:
            logger.error(f"❌ Load failed: {e}", exc_info=True)
            return False

    def verify_load(self, conn: psycopg2.connection, expected_counts: Dict[str, int]):
        """Verify that data was loaded correctly."""
        logger.info("\n🔍 Verifying loaded data...")

        cursor = conn.cursor()
        mismatches = []

        for table, expected_count in expected_counts.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                actual_count = cursor.fetchone()[0]

                if actual_count == expected_count:
                    logger.info(f"  ✅ {table}: {actual_count} rows (expected {expected_count})")
                else:
                    logger.warning(f"  ⚠️  {table}: {actual_count} rows (expected {expected_count})")
                    mismatches.append((table, actual_count, expected_count))

            except psycopg2.Error as e:
                logger.error(f"  ❌ Failed to verify {table}: {e}")

        if mismatches:
            logger.warning(f"\n⚠️  {len(mismatches)} table(s) have row count mismatches:")
            for table, actual, expected in mismatches:
                logger.warning(f"    • {table}: {actual} vs {expected}")
            return False
        else:
            logger.info("✅ All tables verified - row counts match!")
            return True

    def print_summary(self):
        """Print load summary."""
        duration = (self.end_time - self.start_time).total_seconds()

        logger.info("\n" + "="*70)
        logger.info("  LOAD SUMMARY")
        logger.info("="*70)
        logger.info(f"📊 Tables loaded: {len(self.loaded_counts)}")
        logger.info(f"📝 Total rows: {sum(self.loaded_counts.values())}")
        logger.info(f"🗄️  Database: {self.database_url.split('@')[1] if '@' in self.database_url else 'PostgreSQL'}")
        logger.info(f"⏱️  Duration: {duration:.2f} seconds")
        logger.info("\n📋 Rows Loaded by Table:")

        for table, count in sorted(self.loaded_counts.items()):
            logger.info(f"  • {table}: {count} rows")

        logger.info("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Load JSON data into PostgreSQL'
    )
    parser.add_argument(
        '--source',
        required=True,
        help='Source JSON export file'
    )
    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection URL (uses DATABASE_URL env var if not provided)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify data after loading'
    )

    args = parser.parse_args()

    # Verify source exists
    if not os.path.exists(args.source):
        logger.error(f"❌ Source file not found: {args.source}")
        return 1

    # Load data
    loader = PostgreSQLLoader(args.source, args.database_url)

    if loader.load_all(verify=args.verify):
        logger.info("✅ PostgreSQL load completed successfully")
        return 0
    else:
        logger.error("❌ PostgreSQL load failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
