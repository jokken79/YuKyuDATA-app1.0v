#!/usr/bin/env python3
"""
Database and application health check script.

This script performs comprehensive health checks on both SQLite and PostgreSQL
databases, connection pooling, and application endpoints.

Usage:
    python monitoring/health_check.py
    python monitoring/health_check.py --detailed
    python monitoring/health_check.py --postgres-only
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import argparse
import logging
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class HealthChecker:
    """Performs comprehensive health checks."""

    def __init__(self, detailed: bool = False, postgres_only: bool = False):
        """
        Initialize health checker.

        Args:
            detailed: Perform detailed checks
            postgres_only: Only check PostgreSQL (skip SQLite)
        """
        self.detailed = detailed
        self.postgres_only = postgres_only
        self.checks_passed = []
        self.checks_failed = []
        self.checks_warned = []
        self.start_time = None
        self.end_time = None

    def check_sqlite_database(self) -> bool:
        """Check SQLite database health."""
        if self.postgres_only:
            return True

        logger.info("\n🔍 Checking SQLite Database...")

        try:
            import sqlite3

            db_file = 'yukyu.db'

            if not os.path.exists(db_file):
                logger.warning(f"  ⚠️  SQLite database not found: {db_file}")
                self.checks_warned.append("SQLite database not found")
                return True

            # Connect
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # Check tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                logger.error("  ❌ No tables found in SQLite")
                self.checks_failed.append("SQLite has no tables")
                return False

            logger.info(f"  ✅ SQLite has {len(tables)} tables")

            # Check row counts
            total_rows = 0
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_rows += count

                if self.detailed:
                    logger.info(f"     • {table}: {count} rows")

            logger.info(f"  ✅ Total rows: {total_rows}")

            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]

            if result == 'ok':
                logger.info("  ✅ SQLite integrity check: OK")
                self.checks_passed.append("SQLite database integrity")
            else:
                logger.error(f"  ❌ SQLite integrity check failed: {result}")
                self.checks_failed.append(f"SQLite integrity: {result}")
                return False

            conn.close()
            return True

        except Exception as e:
            logger.error(f"  ❌ SQLite check failed: {e}")
            self.checks_failed.append(f"SQLite check: {e}")
            return False

    def check_postgresql_connection(self) -> bool:
        """Check PostgreSQL connection."""
        logger.info("\n🔍 Checking PostgreSQL Connection...")

        try:
            import psycopg2

            database_url = os.getenv(
                'DATABASE_URL',
                'postgresql://yukyu_user:change_me@localhost:5432/yukyu'
            )

            if database_url.startswith('sqlite'):
                logger.info("  ℹ️  PostgreSQL not configured (using SQLite)")
                self.checks_warned.append("PostgreSQL not configured")
                return True

            # Try to connect
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()

            # Check version
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"  ✅ Connected to PostgreSQL")
            logger.info(f"     Version: {version.split(',')[0]}")

            # Check tables
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            if tables:
                logger.info(f"  ✅ PostgreSQL has {len(tables)} tables")
                self.checks_passed.append("PostgreSQL connection")

                # Check row counts
                total_rows = 0
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_rows += count

                    if self.detailed:
                        logger.info(f"     • {table}: {count} rows")

                logger.info(f"  ✅ Total rows: {total_rows}")
            else:
                logger.warning("  ⚠️  PostgreSQL has no tables")
                self.checks_warned.append("PostgreSQL has no tables")

            conn.close()
            return True

        except Exception as e:
            logger.warning(f"  ⚠️  PostgreSQL check failed: {e}")
            self.checks_warned.append(f"PostgreSQL: {e}")
            return True  # Don't fail the overall check

    def check_connection_pool(self) -> bool:
        """Check connection pool status."""
        logger.info("\n🔍 Checking Connection Pool...")

        try:
            import psycopg2

            database_url = os.getenv('DATABASE_URL')

            if not database_url or database_url.startswith('sqlite'):
                logger.info("  ℹ️  PostgreSQL connection pool not active")
                return True

            # Try multiple connections
            pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
            logger.info(f"  ℹ️  Testing connection pool (size={pool_size})...")

            connections = []
            start_time = time.time()

            try:
                for i in range(min(3, pool_size)):
                    conn = psycopg2.connect(database_url)
                    connections.append(conn)

                elapsed = time.time() - start_time
                logger.info(f"  ✅ Successfully created {len(connections)} connections in {elapsed:.2f}s")
                self.checks_passed.append("Connection pool")

            finally:
                for conn in connections:
                    conn.close()

            return True

        except Exception as e:
            logger.warning(f"  ⚠️  Connection pool check failed: {e}")
            self.checks_warned.append(f"Connection pool: {e}")
            return True

    def check_api_endpoints(self) -> bool:
        """Check API endpoint availability."""
        logger.info("\n🔍 Checking API Endpoints...")

        try:
            import requests

            # Check if server is running
            try:
                response = requests.get('http://localhost:8000/health', timeout=2)

                if response.status_code == 200:
                    logger.info("  ✅ Health endpoint reachable")
                    health_data = response.json()

                    if health_data.get('status') == 'healthy':
                        logger.info("  ✅ Application is healthy")
                        self.checks_passed.append("API endpoints")

                        # Check database type
                        db_type = health_data.get('database', {}).get('type')
                        logger.info(f"     Database type: {db_type}")

                        # Check employee count
                        emp_count = health_data.get('database', {}).get('employees_count', 0)
                        logger.info(f"     Employees: {emp_count}")

                        if emp_count > 0:
                            logger.info("  ✅ Data is present")
                        else:
                            logger.warning("  ⚠️  No employees found in database")

                    else:
                        logger.warning(f"  ⚠️  Application status: {health_data.get('status')}")
                        self.checks_warned.append(f"API status: {health_data.get('status')}")

                else:
                    logger.warning(f"  ⚠️  Health endpoint returned {response.status_code}")
                    self.checks_warned.append(f"Health endpoint: {response.status_code}")

            except requests.exceptions.ConnectionError:
                logger.warning("  ⚠️  API server not running on http://localhost:8000")
                logger.info("     Start with: python -m uvicorn main:app --reload")
                self.checks_warned.append("API server not running")

            return True

        except ImportError:
            logger.warning("  ⚠️  requests library not installed (skipping API checks)")
            return True

    def check_file_permissions(self) -> bool:
        """Check file permissions and accessibility."""
        logger.info("\n🔍 Checking File Permissions...")

        try:
            files_to_check = [
                'yukyu.db',
                '.env',
                'main.py',
                'database.py'
            ]

            for file_name in files_to_check:
                if os.path.exists(file_name):
                    if os.access(file_name, os.R_OK):
                        logger.info(f"  ✅ {file_name}: readable")
                    else:
                        logger.warning(f"  ⚠️  {file_name}: not readable")
                        self.checks_warned.append(f"{file_name}: not readable")

            self.checks_passed.append("File permissions")
            return True

        except Exception as e:
            logger.warning(f"  ⚠️  File permission check failed: {e}")
            return True

    def run_all_checks(self) -> bool:
        """Run all health checks."""
        self.start_time = datetime.now()

        logger.info("🏥 Starting Health Checks...\n")

        # Run checks
        self.check_sqlite_database()
        self.check_postgresql_connection()
        self.check_connection_pool()
        self.check_file_permissions()
        self.check_api_endpoints()

        self.end_time = datetime.now()
        self.print_summary()

        return len(self.checks_failed) == 0

    def print_summary(self):
        """Print health check summary."""
        duration = (self.end_time - self.start_time).total_seconds()

        logger.info("\n" + "="*70)
        logger.info("  HEALTH CHECK SUMMARY")
        logger.info("="*70)

        logger.info(f"\n📊 Results:")
        logger.info(f"  ✅ Passed: {len(self.checks_passed)}")
        logger.info(f"  ⚠️  Warned: {len(self.checks_warned)}")
        logger.info(f"  ❌ Failed: {len(self.checks_failed)}")

        if self.checks_passed:
            logger.info(f"\n✅ Passed Checks:")
            for check in self.checks_passed:
                logger.info(f"  • {check}")

        if self.checks_warned:
            logger.info(f"\n⚠️  Warnings:")
            for check in self.checks_warned:
                logger.info(f"  • {check}")

        if self.checks_failed:
            logger.error(f"\n❌ Failed Checks:")
            for check in self.checks_failed:
                logger.error(f"  • {check}")

        logger.info(f"\n⏱️  Duration: {duration:.2f} seconds")

        if len(self.checks_failed) == 0:
            logger.info("\n✅ Health Check PASSED")
        else:
            logger.error("\n❌ Health Check FAILED")

        logger.info("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Perform comprehensive health checks'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed information'
    )
    parser.add_argument(
        '--postgres-only',
        action='store_true',
        help='Check PostgreSQL only (skip SQLite)'
    )

    args = parser.parse_args()

    checker = HealthChecker(args.detailed, args.postgres_only)

    if checker.run_all_checks():
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
