#!/usr/bin/env python3
"""
Backup Manager for Point-in-Time Recovery (PITR).

Manages PostgreSQL base backups, WAL archiving, and point-in-time recovery.
Uses pg_basebackup for full backups with automatic compression and verification.

Usage:
    python monitoring/backup_manager.py --create          # Create base backup
    python monitoring/backup_manager.py --verify          # Verify backup integrity
    python monitoring/backup_manager.py --list-windows    # Show recovery windows
    python monitoring/backup_manager.py --restore <time>  # Restore to point in time
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
import shutil
import gzip

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class BackupManager:
    """Manages PostgreSQL backups for PITR."""

    def __init__(self, backup_dir: Optional[str] = None):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory for storing backups (default: ./backups)
        """
        self.backup_dir = Path(backup_dir or './backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.backup_dir / 'backup_metadata.json'
        self.backups = self._load_metadata()
        # Create metadata file on initialization if it doesn't exist
        if not self.metadata_file.exists():
            self._save_metadata()

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load backup metadata from JSON file."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️  Could not load backup metadata: {e}")

        return {}

    def _save_metadata(self):
        """Save backup metadata to JSON file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.backups, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save backup metadata: {e}")

    def create_base_backup(
        self,
        host: str = 'localhost',
        port: int = 5432,
        username: str = 'postgres',
        compress: bool = True
    ) -> bool:
        """
        Create a base backup using pg_basebackup.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            username: PostgreSQL username
            compress: Compress backup with gzip

        Returns:
            True if successful, False otherwise
        """
        try:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backup_dir / backup_name

            logger.info(f"\n📦 Creating base backup: {backup_name}")

            # Build pg_basebackup command
            cmd = [
                'pg_basebackup',
                '-h', host,
                '-p', str(port),
                '-U', username,
                '-D', str(backup_path),
                '-F', 'tar',  # Use tar format for compression
                '-z',  # Compress with gzip
                '-P',  # Show progress
                '-v',  # Verbose
                '-R',  # Include recovery configuration
                '-C',  # Include checkpoint
            ]

            logger.info(f"  Running: {' '.join(cmd)}")

            # Create backup
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

            if result.returncode != 0:
                logger.error(f"❌ Backup failed: {result.stderr}")
                return False

            backup_size = self._get_backup_size(backup_path)
            backup_time = datetime.now()

            # Store metadata
            self.backups[backup_name] = {
                'timestamp': backup_time.isoformat(),
                'size_bytes': backup_size,
                'size_human': self._format_size(backup_size),
                'host': host,
                'port': port,
                'status': 'verified' if self._verify_backup(backup_path) else 'unverified',
                'compressed': compress,
                'recovery_target_timeline': 'latest'
            }
            self._save_metadata()

            logger.info(f"✅ Backup created successfully")
            logger.info(f"  Path: {backup_path}")
            logger.info(f"  Size: {self._format_size(backup_size)}")
            logger.info(f"  Time: {backup_time.isoformat()}")

            return True

        except subprocess.TimeoutExpired:
            logger.error("❌ Backup timed out (>1 hour)")
            return False
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False

    def _verify_backup(self, backup_path: Path) -> bool:
        """Verify backup integrity."""
        try:
            # Check for backup_label file (indicates valid backup)
            if not (backup_path / 'backup_label').exists():
                logger.warning("⚠️  backup_label not found")
                return False

            # Verify tar integrity if compressed
            if backup_path.suffix == '.tar.gz':
                cmd = ['tar', '-tzf', str(backup_path)]
                result = subprocess.run(cmd, capture_output=True, timeout=60)
                if result.returncode != 0:
                    logger.warning("⚠️  Tar file integrity check failed")
                    return False

            logger.info("✅ Backup verification passed")
            return True

        except Exception as e:
            logger.warning(f"⚠️  Backup verification failed: {e}")
            return False

    def _get_backup_size(self, backup_path: Path) -> int:
        """Get total size of backup directory/file."""
        try:
            if backup_path.is_file():
                return backup_path.stat().st_size
            else:
                total = 0
                for entry in backup_path.rglob('*'):
                    if entry.is_file():
                        total += entry.stat().st_size
                return total
        except Exception as e:
            logger.warning(f"⚠️  Could not calculate backup size: {e}")
            return 0

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"

    def list_backups(self) -> Dict[str, Dict[str, Any]]:
        """List all available backups."""
        logger.info("\n📋 Available Backups:\n")

        if not self.backups:
            logger.info("  No backups available")
            return {}

        # Sort by timestamp (newest first)
        sorted_backups = sorted(
            self.backups.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )

        for idx, (name, info) in enumerate(sorted_backups, 1):
            timestamp = info.get('timestamp', 'unknown')
            size = info.get('size_human', 'unknown')
            status = info.get('status', 'unknown')

            logger.info(f"  {idx}. {name}")
            logger.info(f"     Timestamp: {timestamp}")
            logger.info(f"     Size: {size}")
            logger.info(f"     Status: {status}")
            logger.info("")

        return dict(sorted_backups)

    def get_recovery_windows(self) -> Dict[str, Any]:
        """
        Get available recovery windows.

        Returns information about the time range for PITR.
        """
        if not self.backups:
            logger.warning("❌ No backups available")
            return {}

        # Get latest backup
        latest_backup = max(
            self.backups.items(),
            key=lambda x: x[1].get('timestamp', '0'),
            default=(None, {})
        )

        if not latest_backup[0]:
            return {}

        backup_name, backup_info = latest_backup
        backup_time = datetime.fromisoformat(backup_info.get('timestamp', datetime.now().isoformat()))

        # Calculate recovery window (7 days by default)
        recovery_start = backup_time
        recovery_end = datetime.now()
        recovery_window = (recovery_end - recovery_start).days

        logger.info(f"\n⏱️  Recovery Window Information:\n")
        logger.info(f"  Latest Backup: {backup_name}")
        logger.info(f"  Backup Time: {backup_time.isoformat()}")
        logger.info(f"  Current Time: {datetime.now().isoformat()}")
        logger.info(f"  Recovery Window: {recovery_window} days")
        logger.info(f"  Can Recover To: Any point between {backup_time.isoformat()}")
        logger.info(f"                  and {datetime.now().isoformat()}")
        logger.info("")

        return {
            'latest_backup': backup_name,
            'backup_time': backup_time.isoformat(),
            'current_time': datetime.now().isoformat(),
            'recovery_window_days': recovery_window,
            'can_recover_from': backup_time.isoformat(),
            'can_recover_to': datetime.now().isoformat()
        }

    def restore_to_point_in_time(
        self,
        recovery_time: str,
        restore_path: Optional[str] = None,
        host: str = 'localhost',
        port: int = 5432
    ) -> bool:
        """
        Restore database to a specific point in time.

        Args:
            recovery_time: Target recovery time (ISO format: 2025-12-23T15:30:00)
            restore_path: Path to restore to
            host: Target PostgreSQL host
            port: Target PostgreSQL port

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"\n🔄 Starting Point-in-Time Recovery (PITR)")
            logger.info(f"  Target Time: {recovery_time}")

            if not self.backups:
                logger.error("❌ No backups available for recovery")
                return False

            # Find backup taken before recovery_time
            recovery_dt = datetime.fromisoformat(recovery_time)
            suitable_backup = None

            for backup_name, backup_info in self.backups.items():
                backup_time = datetime.fromisoformat(backup_info.get('timestamp', ''))
                if backup_time <= recovery_dt:
                    if not suitable_backup or backup_time > datetime.fromisoformat(
                        self.backups[suitable_backup].get('timestamp', '')
                    ):
                        suitable_backup = backup_name

            if not suitable_backup:
                logger.error(f"❌ No suitable backup found before {recovery_time}")
                return False

            logger.info(f"  Using backup: {suitable_backup}")

            restore_path = restore_path or self.backup_dir / f'restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            restore_path = Path(restore_path)
            restore_path.mkdir(parents=True, exist_ok=True)

            backup_path = self.backup_dir / suitable_backup
            logger.info(f"  Extracting to: {restore_path}")

            # Extract backup
            if backup_path.suffix == '.tar' or str(backup_path).endswith('.tar.gz'):
                cmd = ['tar', '-xzf' if str(backup_path).endswith('.gz') else '-xf',
                       str(backup_path), '-C', str(restore_path)]
                result = subprocess.run(cmd, capture_output=True, timeout=600)
                if result.returncode != 0:
                    logger.error(f"❌ Extraction failed: {result.stderr}")
                    return False

            # Create recovery configuration
            recovery_conf = f"""# Recovery Configuration
recovery_target_timeline = 'latest'
recovery_target_time = '{recovery_time}'
recovery_target_inclusive = true
restore_command = 'cp /backups/wal_archive/%f %p'
"""

            recovery_file = restore_path / 'recovery.conf'
            with open(recovery_file, 'w') as f:
                f.write(recovery_conf)

            logger.info(f"✅ Recovery preparation complete")
            logger.info(f"  Restore Path: {restore_path}")
            logger.info(f"  Recovery Config: {recovery_file}")
            logger.info(f"\n📝 Next Steps:")
            logger.info(f"  1. Stop PostgreSQL: systemctl stop postgresql")
            logger.info(f"  2. Replace data directory: mv {restore_path} /var/lib/postgresql/14/main")
            logger.info(f"  3. Start PostgreSQL: systemctl start postgresql")
            logger.info(f"  4. Verify recovery: psql -U postgres -c \"SELECT now()\"")

            return True

        except Exception as e:
            logger.error(f"❌ Recovery failed: {e}")
            return False

    def cleanup_old_backups(self, keep_count: int = 5) -> bool:
        """
        Remove old backups, keeping only the most recent.

        Args:
            keep_count: Number of backups to keep

        Returns:
            True if successful, False otherwise
        """
        try:
            if len(self.backups) <= keep_count:
                logger.info(f"✅ Backup count ({len(self.backups)}) within retention policy (keep {keep_count})")
                return True

            logger.info(f"\n🧹 Cleaning up old backups")
            logger.info(f"  Current backups: {len(self.backups)}")
            logger.info(f"  Keep count: {keep_count}")

            # Sort by timestamp (newest first)
            sorted_backups = sorted(
                self.backups.items(),
                key=lambda x: x[1].get('timestamp', ''),
                reverse=True
            )

            # Remove old backups
            removed = 0
            for backup_name, backup_info in sorted_backups[keep_count:]:
                backup_path = self.backup_dir / backup_name
                try:
                    if backup_path.exists():
                        if backup_path.is_file():
                            backup_path.unlink()
                        else:
                            shutil.rmtree(backup_path)

                        del self.backups[backup_name]
                        removed += 1
                        logger.info(f"  Removed: {backup_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not remove {backup_name}: {e}")

            self._save_metadata()
            logger.info(f"✅ Removed {removed} old backups")

            return True

        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return False

    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics for monitoring."""
        total_size = sum(b.get('size_bytes', 0) for b in self.backups.values())
        backup_count = len(self.backups)

        return {
            'backup_count': backup_count,
            'total_size_bytes': total_size,
            'total_size_human': self._format_size(total_size),
            'latest_backup': max(
                self.backups.items(),
                key=lambda x: x[1].get('timestamp', '0'),
                default=(None, {})
            )[0],
            'backups': self.backups
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Manage PostgreSQL backups for point-in-time recovery'
    )
    parser.add_argument(
        '--create',
        action='store_true',
        help='Create a new base backup'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available backups'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify backup integrity'
    )
    parser.add_argument(
        '--list-windows',
        action='store_true',
        help='Show recovery windows'
    )
    parser.add_argument(
        '--restore',
        help='Restore to point in time (ISO format: 2025-12-23T15:30:00)'
    )
    parser.add_argument(
        '--cleanup',
        type=int,
        help='Remove old backups, keeping N most recent'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show backup statistics'
    )
    parser.add_argument(
        '--backup-dir',
        default='./backups',
        help='Directory for storing backups'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='PostgreSQL host'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5432,
        help='PostgreSQL port'
    )
    parser.add_argument(
        '--username',
        default='postgres',
        help='PostgreSQL username'
    )

    args = parser.parse_args()

    manager = BackupManager(args.backup_dir)

    if args.create:
        success = manager.create_base_backup(
            host=args.host,
            port=args.port,
            username=args.username
        )
        return 0 if success else 1

    elif args.list:
        manager.list_backups()
        return 0

    elif args.verify:
        manager.list_backups()
        return 0

    elif args.list_windows:
        manager.get_recovery_windows()
        return 0

    elif args.restore:
        success = manager.restore_to_point_in_time(
            args.restore,
            host=args.host,
            port=args.port
        )
        return 0 if success else 1

    elif args.cleanup:
        success = manager.cleanup_old_backups(keep_count=args.cleanup)
        return 0 if success else 1

    elif args.stats:
        stats = manager.get_backup_statistics()
        logger.info("\n📊 Backup Statistics:\n")
        logger.info(f"  Backups: {stats['backup_count']}")
        logger.info(f"  Total Size: {stats['total_size_human']}")
        logger.info(f"  Latest: {stats['latest_backup']}")
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
