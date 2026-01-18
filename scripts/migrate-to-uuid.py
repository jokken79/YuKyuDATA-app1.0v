#!/usr/bin/env python3

"""
migrate-to-uuid.py
Data migration script to populate UUID values and complete schema migration.
Converts existing composite keys to UUID-based primary keys.
"""

import sqlite3
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

class UUIDMigrator:
    def __init__(self, db_path: str, dry_run: bool = False):
        self.db_path = db_path
        self.dry_run = dry_run
        self.migrations = {}
        self.stats = {}

    def connect(self) -> sqlite3.Connection:
        """Create database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.isolation_level = None  # Autocommit mode
        return conn

    def print_section(self, title: str):
        """Print section header."""
        print(f"\n{Colors.BLUE}{'═' * 60}{Colors.NC}")
        print(f"{Colors.BLUE}  {title}{Colors.NC}")
        print(f"{Colors.BLUE}{'═' * 60}{Colors.NC}")

    def print_status(self, message: str, status: str = "INFO"):
        """Print status message."""
        icon = {
            "INFO": f"{Colors.BLUE}ℹ{Colors.NC}",
            "OK": f"{Colors.GREEN}✓{Colors.NC}",
            "WARN": f"{Colors.YELLOW}⚠{Colors.NC}",
            "ERROR": f"{Colors.RED}✗{Colors.NC}"
        }.get(status, "•")
        print(f"{icon} {message}")

    def migrate_employees(self, conn: sqlite3.Connection) -> bool:
        """Migrate employees table to UUID primary key."""
        c = conn.cursor()

        try:
            self.print_section("Migrating Employees Table")

            # Check if employees already have UUIDs
            c.execute("SELECT COUNT(*) FROM employees WHERE id IS NULL OR id = ''")
            null_count = c.fetchone()[0]

            if null_count == 0:
                self.print_status(f"All employees already have UUIDs", "OK")
                c.execute("SELECT COUNT(*) FROM employees")
                count = c.fetchone()[0]
                self.stats['employees'] = count
                return True

            self.print_status(f"Found {null_count} employees needing UUID migration", "INFO")

            # Get all employees with NULL or empty ids
            c.execute("""
                SELECT rowid, employee_num, year, id FROM employees
                WHERE id IS NULL OR id = ''
            """)
            rows = c.fetchall()

            for idx, row in enumerate(rows, 1):
                rowid = row[0]
                employee_num = row[1]
                year = row[2]
                old_id = row[3]

                # Generate UUID based on employee_num and year
                # This ensures consistency if migration is run multiple times
                composite_key = f"{employee_num}_{year}"
                new_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, composite_key))

                if not self.dry_run:
                    c.execute(
                        "UPDATE employees SET id = ? WHERE rowid = ?",
                        (new_uuid, rowid)
                    )

                if idx % 100 == 0 or idx == len(rows):
                    print(f"  Migrated {idx}/{len(rows)} employees", end='\r')

            if not self.dry_run:
                conn.commit()

            print(f"  ✓ Migrated {len(rows)} employees")

            c.execute("SELECT COUNT(*) FROM employees")
            self.stats['employees'] = c.fetchone()[0]
            return True

        except Exception as e:
            self.print_status(f"Error migrating employees: {e}", "ERROR")
            return False

    def migrate_leave_requests(self, conn: sqlite3.Connection) -> bool:
        """Migrate leave_requests table to UUID primary key."""
        c = conn.cursor()

        try:
            self.print_section("Migrating Leave Requests Table")

            # Check if leave_requests already have UUIDs
            c.execute("SELECT COUNT(*) FROM leave_requests WHERE id IS NULL OR id = ''")
            null_count = c.fetchone()[0]

            if null_count == 0:
                self.print_status(f"All leave requests already have UUIDs", "OK")
                c.execute("SELECT COUNT(*) FROM leave_requests")
                count = c.fetchone()[0]
                self.stats['leave_requests'] = count
                return True

            self.print_status(f"Found {null_count} leave requests needing UUID migration", "INFO")

            # Get all leave_requests with NULL or empty ids
            c.execute("""
                SELECT rowid, employee_num, start_date, end_date FROM leave_requests
                WHERE id IS NULL OR id = ''
            """)
            rows = c.fetchall()

            for idx, row in enumerate(rows, 1):
                rowid = row[0]
                employee_num = row[1]
                start_date = row[2]
                end_date = row[3]

                # Generate UUID based on employee_num and dates
                composite_key = f"{employee_num}_{start_date}_{end_date}_{rowid}"
                new_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, composite_key))

                if not self.dry_run:
                    c.execute(
                        "UPDATE leave_requests SET id = ? WHERE rowid = ?",
                        (new_uuid, rowid)
                    )

                if idx % 100 == 0 or idx == len(rows):
                    print(f"  Migrated {idx}/{len(rows)} leave requests", end='\r')

            if not self.dry_run:
                conn.commit()

            print(f"  ✓ Migrated {len(rows)} leave requests")

            c.execute("SELECT COUNT(*) FROM leave_requests")
            self.stats['leave_requests'] = c.fetchone()[0]
            return True

        except Exception as e:
            self.print_status(f"Error migrating leave_requests: {e}", "ERROR")
            return False

    def migrate_genzai(self, conn: sqlite3.Connection) -> bool:
        """Migrate genzai table."""
        c = conn.cursor()

        try:
            # Check if table has id column
            c.execute("PRAGMA table_info(genzai)")
            columns = {row[1]: row[2] for row in c.fetchall()}

            if 'id' not in columns:
                self.print_status("genzai table doesn't have id column, skipping", "WARN")
                return True

            c.execute("SELECT COUNT(*) FROM genzai WHERE id IS NULL OR id = ''")
            null_count = c.fetchone()[0]

            if null_count == 0:
                c.execute("SELECT COUNT(*) FROM genzai")
                self.stats['genzai'] = c.fetchone()[0]
                return True

            self.print_status(f"Migrating {null_count} genzai records", "INFO")

            c.execute("SELECT rowid, employee_num FROM genzai WHERE id IS NULL OR id = ''")
            rows = c.fetchall()

            for rowid, employee_num in rows:
                new_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"genzai_{employee_num}"))
                if not self.dry_run:
                    c.execute("UPDATE genzai SET id = ? WHERE rowid = ?", (new_uuid, rowid))

            if not self.dry_run:
                conn.commit()

            c.execute("SELECT COUNT(*) FROM genzai")
            self.stats['genzai'] = c.fetchone()[0]
            return True

        except Exception as e:
            self.print_status(f"Error migrating genzai: {e}", "WARN")
            return False

    def migrate_ukeoi(self, conn: sqlite3.Connection) -> bool:
        """Migrate ukeoi table."""
        c = conn.cursor()

        try:
            c.execute("PRAGMA table_info(ukeoi)")
            columns = {row[1]: row[2] for row in c.fetchall()}

            if 'id' not in columns:
                return True

            c.execute("SELECT COUNT(*) FROM ukeoi WHERE id IS NULL OR id = ''")
            null_count = c.fetchone()[0]

            if null_count == 0:
                c.execute("SELECT COUNT(*) FROM ukeoi")
                self.stats['ukeoi'] = c.fetchone()[0]
                return True

            self.print_status(f"Migrating {null_count} ukeoi records", "INFO")

            c.execute("SELECT rowid, employee_num FROM ukeoi WHERE id IS NULL OR id = ''")
            rows = c.fetchall()

            for rowid, employee_num in rows:
                new_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ukeoi_{employee_num}"))
                if not self.dry_run:
                    c.execute("UPDATE ukeoi SET id = ? WHERE rowid = ?", (new_uuid, rowid))

            if not self.dry_run:
                conn.commit()

            c.execute("SELECT COUNT(*) FROM ukeoi")
            self.stats['ukeoi'] = c.fetchone()[0]
            return True

        except Exception as e:
            self.print_status(f"Error migrating ukeoi: {e}", "WARN")
            return False

    def migrate_staff(self, conn: sqlite3.Connection) -> bool:
        """Migrate staff table."""
        c = conn.cursor()

        try:
            c.execute("PRAGMA table_info(staff)")
            columns = {row[1]: row[2] for row in c.fetchall()}

            if 'id' not in columns:
                return True

            c.execute("SELECT COUNT(*) FROM staff WHERE id IS NULL OR id = ''")
            null_count = c.fetchone()[0]

            if null_count == 0:
                c.execute("SELECT COUNT(*) FROM staff")
                self.stats['staff'] = c.fetchone()[0]
                return True

            self.print_status(f"Migrating {null_count} staff records", "INFO")

            c.execute("SELECT rowid, employee_num FROM staff WHERE id IS NULL OR id = ''")
            rows = c.fetchall()

            for rowid, employee_num in rows:
                new_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"staff_{employee_num}"))
                if not self.dry_run:
                    c.execute("UPDATE staff SET id = ? WHERE rowid = ?", (new_uuid, rowid))

            if not self.dry_run:
                conn.commit()

            c.execute("SELECT COUNT(*) FROM staff")
            self.stats['staff'] = c.fetchone()[0]
            return True

        except Exception as e:
            self.print_status(f"Error migrating staff: {e}", "WARN")
            return False

    def migrate_yukyu_usage_details(self, conn: sqlite3.Connection) -> bool:
        """Migrate yukyu_usage_details table."""
        c = conn.cursor()

        try:
            c.execute("PRAGMA table_info(yukyu_usage_details)")
            columns = {row[1]: row[2] for row in c.fetchall()}

            if 'id' not in columns:
                return True

            c.execute("SELECT COUNT(*) FROM yukyu_usage_details WHERE id IS NULL OR id = ''")
            null_count = c.fetchone()[0]

            if null_count == 0:
                c.execute("SELECT COUNT(*) FROM yukyu_usage_details")
                self.stats['yukyu_usage_details'] = c.fetchone()[0]
                return True

            self.print_status(f"Migrating {null_count} usage detail records", "INFO")

            c.execute("""
                SELECT rowid, employee_num, usage_date FROM yukyu_usage_details
                WHERE id IS NULL OR id = ''
            """)
            rows = c.fetchall()

            for rowid, employee_num, usage_date in rows:
                composite_key = f"usage_{employee_num}_{usage_date}_{rowid}"
                new_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, composite_key))
                if not self.dry_run:
                    c.execute(
                        "UPDATE yukyu_usage_details SET id = ? WHERE rowid = ?",
                        (new_uuid, rowid)
                    )

            if not self.dry_run:
                conn.commit()

            c.execute("SELECT COUNT(*) FROM yukyu_usage_details")
            self.stats['yukyu_usage_details'] = c.fetchone()[0]
            return True

        except Exception as e:
            self.print_status(f"Error migrating yukyu_usage_details: {e}", "WARN")
            return False

    def verify_migration(self, conn: sqlite3.Connection) -> bool:
        """Verify all UUIDs are properly populated."""
        self.print_section("Migration Verification")

        c = conn.cursor()
        all_ok = True

        tables_to_check = ['employees', 'leave_requests', 'genzai', 'ukeoi', 'staff', 'yukyu_usage_details']

        for table in tables_to_check:
            try:
                c.execute(f"PRAGMA table_info({table})")
                columns = {row[1]: row[2] for row in c.fetchall()}

                if 'id' not in columns:
                    self.print_status(f"{table}: No id column", "WARN")
                    continue

                c.execute(f"SELECT COUNT(*) FROM {table}")
                total = c.fetchone()[0]

                c.execute(f"SELECT COUNT(*) FROM {table} WHERE id IS NULL OR id = ''")
                null_count = c.fetchone()[0]

                if null_count == 0:
                    self.print_status(f"{table}: ✓ All {total} UUIDs populated", "OK")
                else:
                    self.print_status(f"{table}: ✗ {null_count}/{total} NULL UUIDs", "ERROR")
                    all_ok = False

            except Exception as e:
                self.print_status(f"{table}: Error - {e}", "WARN")

        return all_ok

    def run_migration(self) -> bool:
        """Execute complete UUID migration."""
        print(f"{Colors.BLUE}{'═' * 60}{Colors.NC}")
        print(f"{Colors.BLUE}   UUID DATA MIGRATION{Colors.NC}")
        print(f"{Colors.BLUE}   Database: {self.db_path}{Colors.NC}")
        if self.dry_run:
            print(f"{Colors.YELLOW}   DRY RUN MODE - No changes will be made{Colors.NC}")
        print(f"{Colors.BLUE}{'═' * 60}{Colors.NC}")

        try:
            conn = self.connect()

            # Run migrations
            self.migrate_employees(conn)
            self.migrate_leave_requests(conn)
            self.migrate_genzai(conn)
            self.migrate_ukeoi(conn)
            self.migrate_staff(conn)
            self.migrate_yukyu_usage_details(conn)

            # Verify
            all_ok = self.verify_migration(conn)

            # Print summary
            self.print_section("Migration Summary")

            print(f"\n{Colors.YELLOW}Row Counts by Table:{Colors.NC}")
            for table in sorted(self.stats.keys()):
                count = self.stats[table]
                print(f"  • {table}: {count} rows")

            if all_ok:
                print(f"\n{Colors.GREEN}Migration completed successfully!{Colors.NC}")
                if self.dry_run:
                    print(f"{Colors.YELLOW}DRY RUN: Changes not committed{Colors.NC}")
                return True
            else:
                print(f"\n{Colors.RED}Migration completed with issues!{Colors.NC}")
                return False

        except Exception as e:
            print(f"{Colors.RED}Fatal error: {e}{Colors.NC}")
            return False

        finally:
            if 'conn' in locals():
                conn.close()


def main():
    """Main entry point."""
    import sys

    db_path = "yukyu.db"
    dry_run = False

    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry-run":
            dry_run = True
        else:
            db_path = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == "--dry-run":
        dry_run = True

    if not Path(db_path).exists():
        print(f"{Colors.RED}Error: Database file '{db_path}' not found!{Colors.NC}")
        sys.exit(1)

    migrator = UUIDMigrator(db_path, dry_run=dry_run)
    success = migrator.run_migration()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
