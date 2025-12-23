#!/usr/bin/env python3
"""
WAL Archiving Configuration for PostgreSQL.

Generates PostgreSQL configuration for Write-Ahead Log (WAL) archiving
required for Point-in-Time Recovery (PITR).

This script creates:
1. WAL archive directory
2. archive_command script
3. restore_command script
4. PostgreSQL configuration snippets

Usage:
    python monitoring/wal_archiving_config.py --setup
    python monitoring/wal_archiving_config.py --generate-config
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WALArchivingConfig:
    """Manages WAL archiving configuration."""

    def __init__(self, wal_archive_dir: str = './backups/wal_archive'):
        """
        Initialize WAL archiving configuration.

        Args:
            wal_archive_dir: Directory for WAL files
        """
        self.wal_archive_dir = Path(wal_archive_dir)
        self.postgres_data_dir = Path('/var/lib/postgresql/14/main')  # Adjust version as needed

    def setup_wal_directory(self) -> bool:
        """Create WAL archive directory with proper permissions."""
        try:
            self.wal_archive_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ WAL archive directory created: {self.wal_archive_dir}")

            # Set permissions (readable by postgres user)
            os.chmod(self.wal_archive_dir, 0o700)
            logger.info(f"✅ Directory permissions set to 0700")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to create WAL directory: {e}")
            return False

    def create_archive_command_script(self) -> bool:
        """Create archive_command script."""
        try:
            script_path = self.wal_archive_dir.parent / 'archive_wal.sh'

            script_content = f'''#!/bin/bash
# Archive WAL file to disk
# This script is called by PostgreSQL's archive_command

# %p = full path of file to archive
# %f = file name only

source_file="${{1:0}}"
archive_dir="{self.wal_archive_dir}"

if [ -z "$source_file" ]; then
    echo "$(date): ERROR - No source file specified" >> $archive_dir/archive.log
    exit 1
fi

dest_file="$archive_dir/$(basename $source_file)"

# Copy file to archive directory
if cp "$source_file" "$dest_file" 2>>/tmp/wal_archive_error.log; then
    echo "$(date): Archived $source_file to $dest_file" >> $archive_dir/archive.log
    exit 0
else
    echo "$(date): ERROR - Failed to archive $source_file" >> $archive_dir/archive.log
    exit 1
fi
'''

            with open(script_path, 'w') as f:
                f.write(script_content)

            os.chmod(script_path, 0o755)
            logger.info(f"✅ Archive command script created: {script_path}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to create archive script: {e}")
            return False

    def create_restore_command_script(self) -> bool:
        """Create restore_command script."""
        try:
            script_path = self.wal_archive_dir.parent / 'restore_wal.sh'

            script_content = f'''#!/bin/bash
# Restore WAL file from archive
# This script is called by PostgreSQL's restore_command during recovery

# %p = full path of file to restore
# %f = file name only

source_file="{self.wal_archive_dir}/${{2}}"
dest_file="${{1}}"

if [ -f "$source_file" ]; then
    cp "$source_file" "$dest_file"
    exit 0
else
    exit 1
fi
'''

            with open(script_path, 'w') as f:
                f.write(script_content)

            os.chmod(script_path, 0o755)
            logger.info(f"✅ Restore command script created: {script_path}")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to create restore script: {e}")
            return False

    def generate_postgres_config(self) -> Dict[str, str]:
        """Generate PostgreSQL configuration for WAL archiving."""
        config = {
            '# WAL Archiving Configuration for PITR': '',
            'wal_level': 'replica',
            'max_wal_senders': '3',
            'wal_keep_size': '1GB',
            'archive_mode': 'on',
            'archive_command': f'test ! -f {self.wal_archive_dir}/%f && cp %p {self.wal_archive_dir}/%f',
            'archive_timeout': '300',
            '# Parallel query settings': '',
            'max_parallel_workers_per_gather': '2',
            'max_parallel_workers': '4',
            'max_worker_processes': '4',
        }

        return config

    def generate_recovery_config(self, recovery_time: str) -> str:
        """Generate recovery configuration file."""
        recovery_conf = f'''# PostgreSQL Recovery Configuration
# Used during recovery from backup

# Recovery target
recovery_target_timeline = 'latest'
recovery_target_time = '{recovery_time}'
recovery_target_inclusive = true

# WAL restore command
restore_command = 'cp {self.wal_archive_dir}/%f "%p"'

# Recovery settings
recovery_target_name = ''  # Optional: set if using named restore points
recovery_min_apply_delay = 0
'''

        return recovery_conf

    def print_configuration(self):
        """Print recommended configuration."""
        logger.info("\n" + "=" * 70)
        logger.info("PostgreSQL WAL Archiving Configuration")
        logger.info("=" * 70 + "\n")

        config = self.generate_postgres_config()

        logger.info("📝 Add these settings to postgresql.conf:\n")

        for key, value in config.items():
            if key.startswith('#'):
                logger.info(f"{key}")
            else:
                logger.info(f"{key} = {value}")

        logger.info("\n" + "-" * 70 + "\n")

        logger.info("📁 Directory Structure:\n")
        logger.info(f"  {self.wal_archive_dir}/")
        logger.info(f"    ├── *.backup              (WAL segment files)")
        logger.info(f"    ├── archive.log           (Archive command log)")
        logger.info(f"    └── (numbered segments)   (000000010000000000000001, etc.)")

        logger.info("\n" + "-" * 70 + "\n")

        logger.info("🔧 Next Steps:\n")
        logger.info("  1. Run this script: python monitoring/wal_archiving_config.py --setup")
        logger.info("  2. Add configuration above to /etc/postgresql/14/main/postgresql.conf")
        logger.info("  3. Restart PostgreSQL: systemctl restart postgresql")
        logger.info("  4. Verify archiving: SELECT * FROM pg_stat_archiver;")
        logger.info("  5. Test backup: python monitoring/backup_manager.py --create")

        logger.info("\n" + "=" * 70 + "\n")

    def verify_wal_archiving(self) -> bool:
        """Verify WAL archiving is working."""
        try:
            import subprocess

            # Check if WAL files exist in archive directory
            wal_files = list(self.wal_archive_dir.glob('0*'))

            if wal_files:
                logger.info(f"✅ WAL archiving is working")
                logger.info(f"  Archive directory: {self.wal_archive_dir}")
                logger.info(f"  WAL files archived: {len(wal_files)}")
                return True
            else:
                logger.warning("⚠️  No WAL files found in archive directory")
                logger.info("  This is normal if archiving was just enabled")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to verify WAL archiving: {e}")
            return False

    def get_archive_stats(self) -> Dict[str, Any]:
        """Get statistics about archived WAL files."""
        try:
            wal_files = list(self.wal_archive_dir.glob('0*'))
            total_size = sum(f.stat().st_size for f in wal_files)

            return {
                'archive_directory': str(self.wal_archive_dir),
                'wal_files_archived': len(wal_files),
                'total_size_bytes': total_size,
                'oldest_file': min(
                    (f.stat().st_mtime for f in wal_files),
                    default=None
                ),
                'newest_file': max(
                    (f.stat().st_mtime for f in wal_files),
                    default=None
                )
            }

        except Exception as e:
            logger.error(f"❌ Failed to get archive stats: {e}")
            return {}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Configure PostgreSQL WAL archiving for PITR'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Create WAL archive directory and scripts'
    )
    parser.add_argument(
        '--generate-config',
        action='store_true',
        help='Generate PostgreSQL configuration'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify WAL archiving is working'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show WAL archive statistics'
    )
    parser.add_argument(
        '--wal-dir',
        default='./backups/wal_archive',
        help='WAL archive directory'
    )

    args = parser.parse_args()

    config = WALArchivingConfig(args.wal_dir)

    if args.setup:
        config.setup_wal_directory()
        config.create_archive_command_script()
        config.create_restore_command_script()
        config.print_configuration()
        return 0

    elif args.generate_config:
        config.print_configuration()
        return 0

    elif args.verify:
        config.verify_wal_archiving()
        return 0

    elif args.stats:
        stats = config.get_archive_stats()
        logger.info("\n📊 WAL Archive Statistics:\n")
        logger.info(f"  Directory: {stats.get('archive_directory')}")
        logger.info(f"  Files: {stats.get('wal_files_archived')}")
        logger.info(f"  Total Size: {stats.get('total_size_bytes')} bytes")
        return 0

    else:
        config.print_configuration()
        return 0


if __name__ == '__main__':
    sys.exit(main())
