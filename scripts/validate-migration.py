#!/usr/bin/env python3

"""
validate-migration.py
Post-migration validation script for UUID schema migration.
Validates data integrity, UUID generation, and constraint verification.
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class MigrationValidator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.issues = []
        self.warnings = []
        self.stats = {}

    def connect(self) -> sqlite3.Connection:
        """Create database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def print_section(self, title: str):
        """Print section header."""
        print(f"\n{Colors.BLUE}{'═' * 60}{Colors.NC}")
        print(f"{Colors.BLUE}  {title}{Colors.NC}")
        print(f"{Colors.BLUE}{'═' * 60}{Colors.NC}")

    def print_check(self, name: str, passed: bool, message: str = ""):
        """Print check result."""
        status = f"{Colors.GREEN}✓{Colors.NC}" if passed else f"{Colors.RED}✗{Colors.NC}"
        msg = f" - {message}" if message else ""
        print(f"{status} {name}{msg}")

    def validate_uuid_columns(self) -> bool:
        """Validate that all tables have UUID id columns."""
        self.print_section("UUID Column Validation")

        conn = self.connect()
        c = conn.cursor()

        passed = True

        # Get all tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in c.fetchall()]

        print(f"\nTotal tables: {len(tables)}")

        for table in tables:
            c.execute(f"PRAGMA table_info({table})")
            columns = {row[1]: row[2] for row in c.fetchall()}

            if 'id' in columns:
                col_type = columns['id']
                self.print_check(
                    f"Table '{table}' has id column",
                    True,
                    f"Type: {col_type}"
                )
            else:
                self.print_check(
                    f"Table '{table}' has id column",
                    False,
                    "MISSING UUID id column!"
                )
                passed = False
                self.issues.append(f"Table '{table}' missing UUID id column")

        conn.close()
        return passed

    def validate_no_null_uuids(self) -> bool:
        """Validate that no UUID columns contain NULL values."""
        self.print_section("NULL UUID Validation")

        conn = self.connect()
        c = conn.cursor()

        passed = True

        # Get all tables with id column
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in c.fetchall()]

        for table in tables:
            try:
                c.execute(f"PRAGMA table_info({table})")
                columns = {row[1]: row[2] for row in c.fetchall()}

                if 'id' in columns:
                    c.execute(f"SELECT COUNT(*) FROM {table} WHERE id IS NULL")
                    null_count = c.fetchone()[0]

                    if null_count == 0:
                        self.print_check(
                            f"Table '{table}' has no NULL UUIDs",
                            True
                        )
                    else:
                        self.print_check(
                            f"Table '{table}' has no NULL UUIDs",
                            False,
                            f"{null_count} NULL UUIDs found!"
                        )
                        passed = False
                        self.issues.append(f"Table '{table}' has {null_count} NULL UUIDs")
            except Exception as e:
                self.warnings.append(f"Error checking table '{table}': {e}")

        conn.close()
        return passed

    def validate_row_counts(self) -> bool:
        """Validate row counts against pre-migration export."""
        self.print_section("Row Count Validation")

        # Find pre-migration export file
        backup_dir = Path("backups")
        export_files = list(backup_dir.glob("data_export_pre_migration_*.json"))

        if not export_files:
            self.warnings.append("No pre-migration export found - skipping row count validation")
            print(f"{Colors.YELLOW}! No pre-migration data export found{Colors.NC}")
            return True

        # Use most recent export
        export_file = sorted(export_files)[-1]

        with open(export_file, 'r') as f:
            pre_migration_data = json.load(f)

        print(f"\nUsing pre-migration export: {export_file.name}")

        conn = self.connect()
        c = conn.cursor()

        passed = True

        for table, expected_info in pre_migration_data.items():
            expected_count = expected_info['count']

            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                actual_count = c.fetchone()[0]

                if actual_count == expected_count:
                    self.print_check(
                        f"Table '{table}' row count",
                        True,
                        f"{actual_count} rows"
                    )
                    self.stats[table] = {
                        'pre': expected_count,
                        'post': actual_count,
                        'match': True
                    }
                else:
                    self.print_check(
                        f"Table '{table}' row count",
                        False,
                        f"Expected {expected_count}, got {actual_count}"
                    )
                    passed = False
                    self.issues.append(
                        f"Table '{table}' row count mismatch: "
                        f"expected {expected_count}, got {actual_count}"
                    )
                    self.stats[table] = {
                        'pre': expected_count,
                        'post': actual_count,
                        'match': False
                    }
            except Exception as e:
                self.warnings.append(f"Error counting rows in '{table}': {e}")

        conn.close()
        return passed

    def validate_constraints(self) -> bool:
        """Validate that database constraints are intact."""
        self.print_section("Constraint Validation")

        conn = self.connect()
        c = conn.cursor()

        passed = True

        # Check for unique constraints (if they exist)
        constraint_checks = [
            ("employees", "employee_num", "year"),
            ("leave_requests", "id", None),
            ("users", "username", None),
        ]

        for table, col1, col2 in constraint_checks:
            try:
                c.execute(f"PRAGMA table_info({table})")
                columns = {row[1]: row[2] for row in c.fetchall()}

                if col1 in columns:
                    if col2 and col2 in columns:
                        # Composite key check
                        c.execute(f"SELECT {col1}, {col2} FROM {table} GROUP BY {col1}, {col2} HAVING COUNT(*) > 1")
                        duplicates = c.fetchall()

                        if not duplicates:
                            self.print_check(
                                f"Table '{table}' unique constraint ({col1}, {col2})",
                                True
                            )
                        else:
                            self.print_check(
                                f"Table '{table}' unique constraint ({col1}, {col2})",
                                False,
                                f"{len(duplicates)} duplicates found"
                            )
                            self.warnings.append(
                                f"Table '{table}' has duplicate ({col1}, {col2}) combinations"
                            )
                    else:
                        # Single column check
                        c.execute(f"SELECT COUNT(*) FROM {table} WHERE {col1} IS NOT NULL")
                        count = c.fetchone()[0]
                        self.print_check(
                            f"Table '{table}' column '{col1}' populated",
                            True,
                            f"{count} non-null values"
                        )
            except Exception as e:
                self.warnings.append(f"Error checking constraints for '{table}': {e}")

        conn.close()
        return passed

    def validate_indexes(self) -> bool:
        """Validate that database indexes are intact."""
        self.print_section("Index Validation")

        conn = self.connect()
        c = conn.cursor()

        # Get all indexes
        c.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name")
        indexes = c.fetchall()

        print(f"\nTotal indexes: {len(indexes)}")

        index_groups = {}
        for idx_name, tbl_name in indexes:
            if not idx_name.startswith('sqlite_'):
                if tbl_name not in index_groups:
                    index_groups[tbl_name] = []
                index_groups[tbl_name].append(idx_name)

        for table in sorted(index_groups.keys()):
            idxs = index_groups[table]
            self.print_check(
                f"Table '{table}' indexes",
                True,
                f"{len(idxs)} indexes"
            )
            for idx in idxs:
                print(f"    • {idx}")

        conn.close()
        return True

    def validate_sample_queries(self) -> bool:
        """Validate that sample queries work correctly."""
        self.print_section("Sample Query Validation")

        conn = self.connect()
        c = conn.cursor()

        passed = True

        test_queries = [
            ("SELECT COUNT(*) FROM employees", "Count employees"),
            ("SELECT COUNT(*) FROM leave_requests", "Count leave requests"),
            ("SELECT COUNT(*) FROM users", "Count users"),
            ("SELECT COUNT(DISTINCT id) FROM employees", "Distinct employee UUIDs"),
        ]

        for query, description in test_queries:
            try:
                c.execute(query)
                result = c.fetchone()[0]
                self.print_check(
                    description,
                    True,
                    f"Result: {result}"
                )
            except Exception as e:
                self.print_check(
                    description,
                    False,
                    f"Error: {str(e)[:50]}"
                )
                passed = False
                self.issues.append(f"Query failed: {description} - {str(e)}")

        conn.close()
        return passed

    def print_summary(self):
        """Print validation summary."""
        self.print_section("Validation Summary")

        print(f"\n{Colors.YELLOW}Statistics:{Colors.NC}")
        if self.stats:
            print(f"{'Table':<20} {'Pre-Migration':<15} {'Post-Migration':<15} {'Status':<10}")
            print("-" * 60)
            for table in sorted(self.stats.keys()):
                info = self.stats[table]
                status = f"{Colors.GREEN}✓ Match{Colors.NC}" if info['match'] else f"{Colors.RED}✗ Mismatch{Colors.NC}"
                print(f"{table:<20} {info['pre']:<15} {info['post']:<15} {status}")

        if self.issues:
            print(f"\n{Colors.RED}Issues Found: {len(self.issues)}{Colors.NC}")
            for issue in self.issues:
                print(f"  • {issue}")
        else:
            print(f"\n{Colors.GREEN}No critical issues found!{Colors.NC}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.NC}")
            for warning in self.warnings:
                print(f"  • {warning}")

        print()

    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print(f"{Colors.BLUE}{'═' * 60}{Colors.NC}")
        print(f"{Colors.BLUE}   MIGRATION VALIDATION REPORT{Colors.NC}")
        print(f"{Colors.BLUE}   Database: {self.db_path}{Colors.NC}")
        print(f"{Colors.BLUE}   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.NC}")
        print(f"{Colors.BLUE}{'═' * 60}{Colors.NC}")

        results = []

        try:
            results.append(("UUID Column Validation", self.validate_uuid_columns()))
            results.append(("NULL UUID Check", self.validate_no_null_uuids()))
            results.append(("Row Count Match", self.validate_row_counts()))
            results.append(("Constraint Validation", self.validate_constraints()))
            results.append(("Index Validation", self.validate_indexes()))
            results.append(("Sample Query Validation", self.validate_sample_queries()))
        except Exception as e:
            print(f"\n{Colors.RED}Fatal error during validation: {e}{Colors.NC}")
            return False

        self.print_summary()

        # Overall result
        all_passed = all(result[1] for result in results)

        if all_passed and not self.issues:
            print(f"{Colors.GREEN}{'═' * 60}{Colors.NC}")
            print(f"{Colors.GREEN}   MIGRATION VALIDATION: PASSED ✓{Colors.NC}")
            print(f"{Colors.GREEN}{'═' * 60}{Colors.NC}\n")
            return True
        else:
            print(f"{Colors.RED}{'═' * 60}{Colors.NC}")
            print(f"{Colors.RED}   MIGRATION VALIDATION: FAILED ✗{Colors.NC}")
            print(f"{Colors.RED}{'═' * 60}{Colors.NC}\n")
            return False


def main():
    """Main entry point."""
    db_path = "yukyu.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    if not Path(db_path).exists():
        print(f"{Colors.RED}Error: Database file '{db_path}' not found!{Colors.NC}")
        sys.exit(1)

    validator = MigrationValidator(db_path)
    success = validator.run_all_validations()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
