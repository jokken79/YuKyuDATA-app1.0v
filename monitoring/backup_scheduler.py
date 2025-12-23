#!/usr/bin/env python3
"""
Automated Backup Scheduler for PostgreSQL PITR.

Manages automated backup scheduling, retention policies, and notifications.
Integrates with cron for scheduled execution.

Usage:
    python monitoring/backup_scheduler.py --setup-cron
    python monitoring/backup_scheduler.py --daily-backup
    python monitoring/backup_scheduler.py --cleanup
    python monitoring/backup_scheduler.py --status
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.backup_manager import BackupManager


class BackupScheduler:
    """Manages automated backup scheduling."""

    def __init__(
        self,
        backup_dir: str = './backups',
        schedule_config_file: Optional[str] = None
    ):
        """
        Initialize backup scheduler.

        Args:
            backup_dir: Directory for backups
            schedule_config_file: Configuration file for backup schedule
        """
        self.backup_manager = BackupManager(backup_dir)
        self.backup_dir = Path(backup_dir)
        self.schedule_config_file = schedule_config_file or self.backup_dir / 'backup_schedule.json'
        self.schedule_config = self._load_schedule_config()

    def _load_schedule_config(self) -> Dict[str, Any]:
        """Load backup schedule configuration."""
        try:
            if self.schedule_config_file.exists():
                with open(self.schedule_config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️  Could not load schedule config: {e}")

        return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default backup schedule configuration."""
        return {
            'backup_schedule': {
                'daily': {
                    'enabled': True,
                    'time': '02:00',  # 2 AM UTC
                    'description': 'Daily full backup'
                },
                'hourly_wal': {
                    'enabled': True,
                    'interval': 1,  # Every hour
                    'description': 'Hourly WAL archiving'
                }
            },
            'retention_policy': {
                'daily_backups': 7,  # Keep 7 days of daily backups
                'weekly_backups': 4,  # Keep 4 weeks of weekly backups
                'monthly_backups': 12,  # Keep 12 months of monthly backups
                'total_backup_size_gb': 100  # Maximum total backup size
            },
            'notifications': {
                'on_success': False,
                'on_failure': True,
                'email_to': '',
                'slack_webhook': ''
            },
            'backup_options': {
                'host': 'localhost',
                'port': 5432,
                'username': 'postgres',
                'compress': True,
                'parallel': True
            },
            'last_backup': None,
            'last_cleanup': None
        }

    def _save_schedule_config(self):
        """Save schedule configuration."""
        try:
            self.schedule_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.schedule_config_file, 'w') as f:
                json.dump(self.schedule_config, f, indent=2)
            logger.info(f"✅ Schedule config saved: {self.schedule_config_file}")
        except Exception as e:
            logger.error(f"❌ Failed to save schedule config: {e}")

    def perform_daily_backup(self) -> bool:
        """Perform daily backup."""
        try:
            logger.info(f"\n📦 Starting daily backup at {datetime.now().isoformat()}")

            options = self.schedule_config.get('backup_options', {})

            success = self.backup_manager.create_base_backup(
                host=options.get('host', 'localhost'),
                port=options.get('port', 5432),
                username=options.get('username', 'postgres'),
                compress=options.get('compress', True)
            )

            if success:
                self.schedule_config['last_backup'] = datetime.now().isoformat()
                self._save_schedule_config()

                # Send success notification if enabled
                if self.schedule_config.get('notifications', {}).get('on_success'):
                    self._send_notification(
                        'Backup Success',
                        'Daily backup completed successfully'
                    )

                logger.info("✅ Daily backup completed")
                return True
            else:
                # Send failure notification
                if self.schedule_config.get('notifications', {}).get('on_failure'):
                    self._send_notification(
                        'Backup Failed',
                        'Daily backup failed. Check logs for details.'
                    )

                logger.error("❌ Daily backup failed")
                return False

        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False

    def cleanup_old_backups(self) -> bool:
        """Clean up old backups according to retention policy."""
        try:
            logger.info(f"\n🧹 Starting backup cleanup at {datetime.now().isoformat()}")

            policy = self.schedule_config.get('retention_policy', {})
            keep_count = policy.get('daily_backups', 7)

            logger.info(f"  Retention policy: keep {keep_count} daily backups")

            success = self.backup_manager.cleanup_old_backups(keep_count=keep_count)

            if success:
                self.schedule_config['last_cleanup'] = datetime.now().isoformat()
                self._save_schedule_config()
                logger.info("✅ Backup cleanup completed")
                return True
            else:
                logger.error("❌ Backup cleanup failed")
                return False

        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return False

    def generate_cron_schedule(self) -> str:
        """Generate cron schedule entries."""
        cron_entries = []

        schedule = self.schedule_config.get('backup_schedule', {})

        # Daily backup cron entry
        if schedule.get('daily', {}).get('enabled'):
            time_str = schedule.get('daily', {}).get('time', '02:00')
            hour, minute = time_str.split(':')
            cron_entries.append(
                f"{minute} {hour} * * * /usr/bin/python3 {Path(__file__).parent}/backup_scheduler.py --daily-backup"
            )

        # Cleanup cron entry (weekly at Sunday 3 AM)
        cron_entries.append(
            f"0 3 * * 0 /usr/bin/python3 {Path(__file__).parent}/backup_scheduler.py --cleanup"
        )

        # Status check cron entry (daily at 8 AM)
        cron_entries.append(
            f"0 8 * * * /usr/bin/python3 {Path(__file__).parent}/backup_scheduler.py --status"
        )

        return '\n'.join(cron_entries)

    def setup_cron_schedule(self) -> bool:
        """Setup cron schedule for automated backups."""
        try:
            cron_entries = self.generate_cron_schedule()

            logger.info("\n📅 Generated Cron Schedule:\n")
            logger.info(cron_entries)
            logger.info("")

            logger.info("To install, run:")
            logger.info(f"  crontab -e")
            logger.info(f"\nThen add these lines:\n")
            logger.info(cron_entries)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup cron: {e}")
            return False

    def get_backup_status(self) -> Dict[str, Any]:
        """Get backup status for monitoring."""
        try:
            stats = self.backup_manager.get_backup_statistics()
            last_backup = self.schedule_config.get('last_backup')
            last_cleanup = self.schedule_config.get('last_cleanup')

            status = {
                'timestamp': datetime.now().isoformat(),
                'last_backup': last_backup,
                'last_cleanup': last_cleanup,
                'backup_stats': stats,
                'schedule_config': self.schedule_config
            }

            return status

        except Exception as e:
            logger.error(f"❌ Failed to get status: {e}")
            return {}

    def print_backup_status(self):
        """Print backup status."""
        status = self.get_backup_status()

        logger.info("\n" + "=" * 70)
        logger.info("PostgreSQL Backup Status")
        logger.info("=" * 70 + "\n")

        logger.info(f"Timestamp: {status.get('timestamp')}")
        logger.info(f"Last Backup: {status.get('last_backup', 'Never')}")
        logger.info(f"Last Cleanup: {status.get('last_cleanup', 'Never')}")

        stats = status.get('backup_stats', {})
        logger.info(f"\nBackup Statistics:")
        logger.info(f"  Count: {stats.get('backup_count', 0)}")
        logger.info(f"  Total Size: {stats.get('total_size_human', 'unknown')}")
        logger.info(f"  Latest: {stats.get('latest_backup', 'none')}")

        logger.info(f"\nRetention Policy:")
        policy = self.schedule_config.get('retention_policy', {})
        logger.info(f"  Daily: {policy.get('daily_backups', 7)} days")
        logger.info(f"  Weekly: {policy.get('weekly_backups', 4)} weeks")
        logger.info(f"  Monthly: {policy.get('monthly_backups', 12)} months")

        logger.info("\n" + "=" * 70 + "\n")

    def _send_notification(self, subject: str, message: str):
        """Send backup notification."""
        notifications = self.schedule_config.get('notifications', {})

        # Log notification
        logger.info(f"📧 Notification: {subject}")
        logger.info(f"   {message}")

        # TODO: Implement email/Slack notifications

    def verify_backup_dependencies(self) -> bool:
        """Verify all backup dependencies are available."""
        try:
            required_tools = ['pg_basebackup', 'pg_restore', 'tar']

            missing = []
            for tool in required_tools:
                result = subprocess.run(
                    ['which', tool],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    missing.append(tool)

            if missing:
                logger.error(f"❌ Missing tools: {', '.join(missing)}")
                return False

            logger.info("✅ All backup dependencies available")
            return True

        except Exception as e:
            logger.warning(f"⚠️  Could not verify dependencies: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage automated PostgreSQL backups'
    )
    parser.add_argument(
        '--setup-cron',
        action='store_true',
        help='Setup cron schedule for automated backups'
    )
    parser.add_argument(
        '--daily-backup',
        action='store_true',
        help='Perform daily backup'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up old backups'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show backup status'
    )
    parser.add_argument(
        '--verify-deps',
        action='store_true',
        help='Verify backup dependencies'
    )
    parser.add_argument(
        '--backup-dir',
        default='./backups',
        help='Backup directory'
    )

    args = parser.parse_args()

    scheduler = BackupScheduler(args.backup_dir)

    if args.setup_cron:
        scheduler.setup_cron_schedule()
        return 0

    elif args.daily_backup:
        success = scheduler.perform_daily_backup()
        return 0 if success else 1

    elif args.cleanup:
        success = scheduler.cleanup_old_backups()
        return 0 if success else 1

    elif args.status:
        scheduler.print_backup_status()
        return 0

    elif args.verify_deps:
        success = scheduler.verify_backup_dependencies()
        return 0 if success else 1

    else:
        scheduler.print_backup_status()
        return 0


if __name__ == '__main__':
    sys.exit(main())
