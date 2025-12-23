#!/usr/bin/env python3
"""
Export SQLite database to JSON format for safe migration to PostgreSQL.

This script creates a complete backup of all SQLite tables in JSON format,
which can be used to restore data to PostgreSQL or as a fallback backup.

Usage:
    python scripts/dump_sqlite_to_json.py
    python scripts/dump_sqlite_to_json.py --source custom_db.db --output backup.json
"""

import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
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


class SQLiteDumper:
    """Exports SQLite database to JSON format."""

    def __init__(self, source_db: str, output_file: str):
        """
        Initialize dumper.

        Args:
            source_db: Path to SQLite database file
            output_file: Path to output JSON file
        """
        self.source_db = source_db
        self.output_file = output_file
        self.data = {}
        self.row_counts = {}
        self.start_time = None
        self.end_time = None

    def connect(self) -> sqlite3.Connection:
        """Create database connection."""
        try:
            conn = sqlite3.connect(self.source_db)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to connect to SQLite: {e}")
            raise

    def get_tables(self, conn: sqlite3.Connection) -> List[str]:
        """Get list of all tables in database."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
        return tables

    def dump_table(self, conn: sqlite3.Connection, table_name: str) -> List[Dict[str, Any]]:
        """Dump a single table to list of dictionaries."""
        cursor = conn.cursor()

        try:
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            # Get all data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Convert to list of dicts
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            self.row_counts[table_name] = len(data)
            logger.info(f"  ✅ {table_name}: {len(data)} rows")

            return data

        except sqlite3.Error as e:
            logger.error(f"  ❌ Failed to dump {table_name}: {e}")
            raise

    def dump_all(self) -> bool:
        """Dump all tables to JSON."""
        self.start_time = datetime.now()

        try:
            logger.info(f"🔄 Starting SQLite dump from: {self.source_db}")

            conn = self.connect()
            tables = self.get_tables(conn)

            if not tables:
                logger.warning("⚠️  No tables found in database")
                return False

            logger.info("📥 Dumping tables to JSON...")

            for table in tables:
                self.data[table] = self.dump_table(conn, table)

            conn.close()

            # Write to JSON file
            self.write_json()

            self.end_time = datetime.now()
            self.print_summary()

            return True

        except Exception as e:
            logger.error(f"❌ Dump failed: {e}", exc_info=True)
            return False

    def write_json(self):
        """Write data to JSON file with metadata."""
        try:
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "source_database": self.source_db,
                "total_tables": len(self.data),
                "total_rows": sum(self.row_counts.values()),
                "row_counts": self.row_counts,
                "tables": self.data
            }

            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"✅ JSON written to: {self.output_file}")

        except Exception as e:
            logger.error(f"❌ Failed to write JSON: {e}")
            raise

    def print_summary(self):
        """Print dump summary."""
        duration = (self.end_time - self.start_time).total_seconds()

        logger.info("\n" + "="*70)
        logger.info("  DUMP SUMMARY")
        logger.info("="*70)
        logger.info(f"📊 Tables dumped: {len(self.data)}")
        logger.info(f"📝 Total rows: {sum(self.row_counts.values())}")
        logger.info(f"📄 Output file: {self.output_file}")
        logger.info(f"💾 File size: {os.path.getsize(self.output_file) / 1024 / 1024:.2f} MB")
        logger.info(f"⏱️  Duration: {duration:.2f} seconds")
        logger.info("\n📋 Row Counts by Table:")

        for table, count in sorted(self.row_counts.items()):
            logger.info(f"  • {table}: {count} rows")

        logger.info("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Export SQLite database to JSON format'
    )
    parser.add_argument(
        '--source',
        default='yukyu.db',
        help='Source SQLite database file (default: yukyu.db)'
    )
    parser.add_argument(
        '--output',
        default=f'data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        help='Output JSON file (default: data_export_TIMESTAMP.json)'
    )

    args = parser.parse_args()

    # Verify source exists
    if not os.path.exists(args.source):
        logger.error(f"❌ Source database not found: {args.source}")
        return 1

    # Create backup
    dumper = SQLiteDumper(args.source, args.output)

    if dumper.dump_all():
        logger.info("✅ SQLite dump completed successfully")
        return 0
    else:
        logger.error("❌ SQLite dump failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
