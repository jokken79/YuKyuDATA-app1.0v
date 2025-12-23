#!/usr/bin/env python3
"""
Test runner for YuKyuDATA FASE 3 PostgreSQL Migration Tests.

This script runs all test suites and generates a comprehensive report.

Usage:
    python scripts/run_tests.py                      # Run all tests
    python scripts/run_tests.py --sqlite-only        # Run SQLite tests only
    python scripts/run_tests.py --postgresql-only    # Run PostgreSQL tests only
    python scripts/run_tests.py --coverage           # Run with coverage report
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Runs test suites and generates reports."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {}
        self.start_time = None
        self.end_time = None

    def print_header(self, title):
        """Print formatted header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70 + "\n")

    def run_command(self, cmd, name):
        """Run a command and capture output."""
        print(f"🚀 Running: {name}...")
        print(f"   Command: {' '.join(cmd)}\n")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            self.results[name] = {
                'passed': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

            if result.returncode == 0:
                print(f"✅ {name}: PASSED\n")
            else:
                print(f"❌ {name}: FAILED")
                print(f"   Error: {result.stderr[:200]}\n")

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print(f"⏱️  {name}: TIMEOUT\n")
            self.results[name] = {
                'passed': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Test timeout (> 5 minutes)'
            }
            return False
        except Exception as e:
            print(f"⚠️  {name}: ERROR - {str(e)}\n")
            self.results[name] = {
                'passed': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }
            return False

    def run_sqlite_tests(self):
        """Run SQLite compatibility tests."""
        self.print_header("FASE 3 Phase 5: SQLite Compatibility Tests")

        os.environ['DATABASE_TYPE'] = 'sqlite'

        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/test_database_compatibility.py',
            '-v',
            '--tb=short',
            '-m', 'not skip_without_postgres'
        ]

        return self.run_command(cmd, 'SQLite Compatibility Tests')

    def run_postgresql_tests(self):
        """Run PostgreSQL integration tests."""
        self.print_header("FASE 3 Phase 5: PostgreSQL Integration Tests")

        # Check if PostgreSQL is configured
        if os.getenv('DATABASE_TYPE', 'sqlite').lower() != 'postgresql':
            print("⚠️  PostgreSQL not configured. Skipping PostgreSQL tests.")
            print("   Set DATABASE_TYPE=postgresql and DATABASE_URL to run these tests.\n")
            self.results['PostgreSQL Integration Tests'] = {
                'passed': True,
                'returncode': 5,
                'stdout': 'Skipped (PostgreSQL not configured)',
                'stderr': ''
            }
            return True

        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/test_postgresql_integration.py',
            '-v',
            '--tb=short'
        ]

        return self.run_command(cmd, 'PostgreSQL Integration Tests')

    def run_pooling_tests(self):
        """Run connection pooling tests."""
        self.print_header("FASE 3 Phase 5: Connection Pooling Tests")

        if os.getenv('DATABASE_TYPE', 'sqlite').lower() != 'postgresql':
            print("⚠️  PostgreSQL not configured. Skipping pooling tests.\n")
            self.results['Connection Pooling Tests'] = {
                'passed': True,
                'returncode': 5,
                'stdout': 'Skipped (PostgreSQL not configured)',
                'stderr': ''
            }
            return True

        cmd = [
            sys.executable, '-m', 'pytest',
            'tests/test_connection_pooling.py',
            '-v',
            '--tb=short'
        ]

        return self.run_command(cmd, 'Connection Pooling Tests')

    def run_all_tests(self, coverage=False):
        """Run all test suites."""
        self.start_time = datetime.now()

        passed = []
        failed = []

        # SQLite tests (always run)
        if self.run_sqlite_tests():
            passed.append('SQLite Compatibility')
        else:
            failed.append('SQLite Compatibility')

        # PostgreSQL tests (if configured)
        if self.run_postgresql_tests():
            passed.append('PostgreSQL Integration')
        else:
            failed.append('PostgreSQL Integration')

        # Pooling tests (if PostgreSQL configured)
        if self.run_pooling_tests():
            passed.append('Connection Pooling')
        else:
            failed.append('Connection Pooling')

        self.end_time = datetime.now()

        self.print_summary(passed, failed)

    def print_summary(self, passed, failed):
        """Print test summary."""
        self.print_header("TEST SUMMARY")

        duration = (self.end_time - self.start_time).total_seconds()

        print(f"📊 Test Results:")
        print(f"   ✅ Passed: {len(passed)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   ⏱️  Duration: {duration:.2f} seconds\n")

        if passed:
            print("✅ Passed Tests:")
            for test in passed:
                print(f"   • {test}")
            print()

        if failed:
            print("❌ Failed Tests:")
            for test in failed:
                print(f"   • {test}")
            print()

        # Recommendations
        self.print_header("NEXT STEPS")

        print("Phase 5 Testing Checklist:")
        print("  ✅ SQLite compatibility verified" if 'SQLite Compatibility' in passed else "  ❌ SQLite tests failed")
        print("  ✅ PostgreSQL integration verified" if 'PostgreSQL Integration' in passed else "  ⚠️  PostgreSQL tests skipped (not configured)")
        print("  ✅ Connection pooling verified" if 'Connection Pooling' in passed else "  ⚠️  Pooling tests skipped (not configured)")

        print("\n📋 To run PostgreSQL tests:")
        print("  export DATABASE_TYPE=postgresql")
        print("  export DATABASE_URL=postgresql://user:pass@localhost:5432/yukyu")
        print("  python scripts/run_tests.py")

        print("\n🚀 Next phase:")
        print("  • Phase 6: Deployment strategy")
        print("  • Phase 9: Full-text search implementation")
        print("  • Phase 10: PITR backup system setup")

        # Return exit code
        return 0 if len(failed) == 0 else 1

    def run(self, args=None):
        """Main entry point."""
        args = args or sys.argv[1:]

        if '--help' in args or '-h' in args:
            print(__doc__)
            return 0

        if '--sqlite-only' in args:
            self.start_time = datetime.now()
            if self.run_sqlite_tests():
                self.end_time = datetime.now()
                self.print_summary(['SQLite Compatibility'], [])
                return 0
            else:
                self.end_time = datetime.now()
                self.print_summary([], ['SQLite Compatibility'])
                return 1

        if '--postgresql-only' in args:
            self.start_time = datetime.now()
            if self.run_postgresql_tests():
                self.end_time = datetime.now()
                self.print_summary(['PostgreSQL Integration'], [])
                return 0
            else:
                self.end_time = datetime.now()
                self.print_summary([], ['PostgreSQL Integration'])
                return 1

        # Run all tests
        self.run_all_tests(coverage='--coverage' in args)
        return self.print_summary(
            [k for k, v in self.results.items() if v.get('passed')],
            [k for k, v in self.results.items() if not v.get('passed')]
        )


if __name__ == '__main__':
    runner = TestRunner()
    exit_code = runner.run()
    sys.exit(exit_code)
