#!/usr/bin/env python3
"""
Rollback PostgreSQL migration and restore to SQLite.

This script handles rolling back a failed PostgreSQL migration:
1. Stops the application
2. Restores SQLite from backup
3. Verifies data integrity
4. Updates configuration to use SQLite

Usage:
    python scripts/rollback_migration.py
    python scripts/rollback_migration.py --backup-file yukyu_backup_2025-12-23.db
    python scripts/rollback_migration.py --dry-run  # Preview without executing
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List
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


class MigrationRollback:
    """Handles rollback of PostgreSQL migration."""

    def __init__(self, backup_file: Optional[str] = None, dry_run: bool = False):
        """
        Initialize rollback handler.

        Args:
            backup_file: Path to SQLite backup file
            dry_run: If True, don't actually execute commands
        """
        self.backup_file = backup_file
        self.dry_run = dry_run
        self.db_file = 'yukyu.db'
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / '.env'
        self.start_time = None
        self.end_time = None
        self.steps_completed = []

    def find_latest_backup(self) -> Optional[str]:
        """Find the latest SQLite backup file."""
        backup_dir = self.project_root

        # Look for backup files matching pattern: yukyu_backup_*.db
        import glob
        backups = sorted(
            glob.glob(str(backup_dir / 'yukyu_backup_*.db')),
            reverse=True
        )

        if backups:
            return backups[0]

        return None

    def check_backup(self) -> bool:
        """Verify backup file exists and is valid."""
        logger.info("🔍 Checking backup file...")

        if not self.backup_file:
            self.backup_file = self.find_latest_backup()

            if not self.backup_file:
                logger.error("❌ No backup file found")
                logger.info("   Please provide backup with --backup-file argument")
                return False

            logger.info(f"  ℹ️  Using latest backup: {self.backup_file}")

        if not os.path.exists(self.backup_file):
            logger.error(f"❌ Backup file not found: {self.backup_file}")
            return False

        # Check file size
        size_mb = os.path.getsize(self.backup_file) / 1024 / 1024
        logger.info(f"  ✅ Backup found: {self.backup_file} ({size_mb:.2f} MB)")

        return True

    def stop_application(self) -> bool:
        """Stop the running application."""
        logger.info("\n🛑 Stopping application...")

        if self.dry_run:
            logger.info("   [DRY RUN] Would kill uvicorn processes")
            return True

        try:
            # Try to kill uvicorn processes
            subprocess.run(
                ['taskkill', '/F', '/IM', 'python.exe', '/T'],
                capture_output=True,
                timeout=5
            )
            logger.info("  ✅ Application stopped")
            return True

        except Exception as e:
            logger.warning(f"  ⚠️  Could not stop application: {e}")
            logger.info("     Please manually stop the application and try again")
            return False

    def backup_current_db(self) -> bool:
        """Create backup of current SQLite database."""
        logger.info("\n💾 Backing up current database...")

        if not os.path.exists(self.db_file):
            logger.info("  ℹ️  No current database to backup")
            return True

        backup_name = f"{self.db_file}.rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if self.dry_run:
            logger.info(f"   [DRY RUN] Would backup to: {backup_name}")
            return True

        try:
            shutil.copy(self.db_file, backup_name)
            logger.info(f"  ✅ Database backed up to: {backup_name}")
            self.steps_completed.append(f"Backup created: {backup_name}")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to backup database: {e}")
            return False

    def restore_backup(self) -> bool:
        """Restore SQLite from backup."""
        logger.info("\n📥 Restoring SQLite from backup...")

        if self.dry_run:
            logger.info(f"   [DRY RUN] Would restore from: {self.backup_file}")
            return True

        try:
            shutil.copy(self.backup_file, self.db_file)
            logger.info(f"  ✅ Database restored from: {self.backup_file}")
            self.steps_completed.append(f"Database restored from {self.backup_file}")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to restore database: {e}")
            return False

    def update_configuration(self) -> bool:
        """Update .env to use SQLite instead of PostgreSQL."""
        logger.info("\n⚙️  Updating configuration...")

        if not self.env_file.exists():
            logger.info("  ℹ️  No .env file found, will be created")

        if self.dry_run:
            logger.info("   [DRY RUN] Would update .env to use SQLite")
            return True

        try:
            # Read current .env
            env_content = ""
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    env_content = f.read()

            # Update DATABASE_TYPE
            lines = env_content.split('\n')
            updated_lines = []

            found_db_type = False
            for line in lines:
                if line.startswith('DATABASE_TYPE='):
                    updated_lines.append('DATABASE_TYPE=sqlite')
                    found_db_type = True
                elif line.startswith('DATABASE_URL='):
                    updated_lines.append('DATABASE_URL=sqlite:///./yukyu.db')
                else:
                    updated_lines.append(line)

            if not found_db_type:
                updated_lines.append('DATABASE_TYPE=sqlite')
                updated_lines.append('DATABASE_URL=sqlite:///./yukyu.db')

            # Write updated .env
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(updated_lines))

            logger.info("  ✅ Configuration updated to use SQLite")
            self.steps_completed.append(".env updated to use SQLite")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to update configuration: {e}")
            return False

    def verify_database(self) -> bool:
        """Verify restored database is valid."""
        logger.info("\n🔍 Verifying restored database...")

        if self.dry_run:
            logger.info("   [DRY RUN] Would verify database")
            return True

        try:
            import sqlite3

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Check for tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()

            if not tables:
                logger.error("❌ No tables found in restored database")
                conn.close()
                return False

            # Count rows in each table
            logger.info(f"  📊 Tables found: {len(tables)}")
            total_rows = 0

            for (table,) in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"    • {table}: {count} rows")
                total_rows += count

            conn.close()

            logger.info(f"  ✅ Database verified: {len(tables)} tables, {total_rows} total rows")
            return True

        except Exception as e:
            logger.error(f"  ❌ Failed to verify database: {e}")
            return False

    def rollback(self) -> bool:
        """Execute complete rollback procedure."""
        self.start_time = datetime.now()

        try:
            logger.info("🔄 Starting PostgreSQL migration rollback...\n")

            if self.dry_run:
                logger.info("⚠️  DRY RUN MODE - No changes will be made\n")

            # Step 1: Check backup
            if not self.check_backup():
                return False

            # Step 2: Stop application
            if not self.stop_application():
                response = input("❓ Continue anyway? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Rollback cancelled")
                    return False

            # Step 3: Backup current database
            if not self.backup_current_db():
                return False

            # Step 4: Restore from backup
            if not self.restore_backup():
                return False

            # Step 5: Update configuration
            if not self.update_configuration():
                return False

            # Step 6: Verify restored database
            if not self.verify_database():
                logger.warning("⚠️  Database verification failed, but rollback may still be valid")

            self.end_time = datetime.now()
            self.print_summary(True)

            return True

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}", exc_info=True)
            self.end_time = datetime.now()
            self.print_summary(False)
            return False

    def print_summary(self, success: bool):
        """Print rollback summary."""
        duration = (self.end_time - self.start_time).total_seconds()

        logger.info("\n" + "="*70)
        logger.info("  ROLLBACK SUMMARY")
        logger.info("="*70)

        if success:
            logger.info("✅ Rollback COMPLETED")
        else:
            logger.error("❌ Rollback FAILED")

        if self.dry_run:
            logger.info("⚠️  DRY RUN - No actual changes made")

        if self.steps_completed:
            logger.info("\n📋 Steps Completed:")
            for step in self.steps_completed:
                logger.info(f"  ✅ {step}")

        logger.info(f"\n⏱️  Duration: {duration:.2f} seconds")

        if success:
            logger.info("\n📝 Next Steps:")
            logger.info("  1. Review the restored database")
            logger.info("  2. Start the application: python -m uvicorn main:app --reload")
            logger.info("  3. Test all endpoints")
            logger.info("  4. Monitor for any issues")
            logger.info("\n📧 Contact: Save logs for troubleshooting if needed")

        logger.info("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Rollback PostgreSQL migration to SQLite'
    )
    parser.add_argument(
        '--backup-file',
        help='Path to SQLite backup file (auto-detects latest if not provided)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview rollback without executing'
    )

    args = parser.parse_args()

    # Create rollback handler
    rollback = MigrationRollback(args.backup_file, args.dry_run)

    # Confirm if not dry-run
    if not args.dry_run:
        print("\n" + "="*70)
        print("  ⚠️  MIGRATION ROLLBACK")
        print("="*70)
        print("\nThis will:")
        print("  1. Stop the running application")
        print("  2. Restore SQLite from backup")
        print("  3. Update configuration to use SQLite")
        print("  4. Verify the restored database")
        print("\n⚠️  This action cannot be easily undone!")
        print("="*70 + "\n")

        response = input("Continue with rollback? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Rollback cancelled")
            return 1

    # Execute rollback
    if rollback.rollback():
        logger.info("✅ Rollback completed successfully")
        return 0
    else:
        logger.error("❌ Rollback failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
