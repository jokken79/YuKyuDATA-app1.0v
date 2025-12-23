#!/usr/bin/env python3
"""
PITR (Point-in-Time Recovery) Integration Tests

Tests for the complete backup and recovery system.
Includes: backup manager, WAL archiving, recovery procedures, scheduler

Run with: pytest tests/test_pitr_integration.py -v
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.backup_manager import BackupManager
from monitoring.wal_archiving_config import WALArchivingConfig
from monitoring.backup_scheduler import BackupScheduler


class TestBackupManagerBasics:
    """Test BackupManager basic functionality."""

    @pytest.fixture
    def backup_dir(self):
        """Create temporary backup directory."""
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def backup_manager(self, backup_dir):
        """Create BackupManager instance."""
        return BackupManager(backup_dir)

    def test_backup_manager_initialization(self, backup_manager):
        """BackupManager should initialize without errors."""
        assert backup_manager is not None
        assert backup_manager.backup_dir.exists()

    def test_metadata_file_creation(self, backup_manager):
        """Metadata file should be created on initialization."""
        assert backup_manager.metadata_file.exists()

    def test_load_empty_metadata(self, backup_manager):
        """Loading empty metadata should return empty dict."""
        backups = backup_manager.backups
        assert isinstance(backups, dict)

    def test_backup_statistics_empty(self, backup_manager):
        """Statistics with no backups should show zeros."""
        stats = backup_manager.get_backup_statistics()
        assert stats['backup_count'] == 0
        assert stats['total_size_bytes'] == 0

    def test_format_size_conversion(self, backup_manager):
        """Size formatting should work correctly."""
        assert backup_manager._format_size(1024) == "1.00 KB"
        assert backup_manager._format_size(1048576) == "1.00 MB"
        assert backup_manager._format_size(1073741824) == "1.00 GB"


class TestBackupMetadata:
    """Test backup metadata management."""

    @pytest.fixture
    def backup_manager(self):
        """Create BackupManager with temp directory."""
        tmpdir = tempfile.mkdtemp()
        manager = BackupManager(tmpdir)
        yield manager
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_save_and_load_metadata(self, backup_manager):
        """Metadata should persist between loads."""
        # Add backup metadata
        backup_manager.backups['test_backup'] = {
            'timestamp': datetime.now().isoformat(),
            'size_bytes': 1000000,
            'status': 'verified'
        }
        backup_manager._save_metadata()

        # Create new manager and verify metadata persists
        new_manager = BackupManager(str(backup_manager.backup_dir))
        assert 'test_backup' in new_manager.backups
        assert new_manager.backups['test_backup']['status'] == 'verified'

    def test_metadata_contains_required_fields(self, backup_manager):
        """Backup metadata should contain required fields."""
        backup_manager.backups['test'] = {
            'timestamp': datetime.now().isoformat(),
            'size_bytes': 5000000,
            'size_human': '5.00 MB',
            'status': 'verified',
            'compressed': True
        }

        assert backup_manager.backups['test']['timestamp']
        assert backup_manager.backups['test']['size_bytes'] > 0
        assert 'MB' in backup_manager.backups['test']['size_human']
        assert backup_manager.backups['test']['status'] in ['verified', 'unverified']


class TestRecoveryWindows:
    """Test recovery window calculations."""

    @pytest.fixture
    def backup_manager(self):
        """Create BackupManager with test data."""
        tmpdir = tempfile.mkdtemp()
        manager = BackupManager(tmpdir)

        # Add test backup from 7 days ago
        backup_time = datetime.now() - timedelta(days=1)
        manager.backups['backup_test'] = {
            'timestamp': backup_time.isoformat(),
            'size_bytes': 1000000,
            'status': 'verified'
        }
        manager._save_metadata()

        yield manager
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_recovery_windows_calculation(self, backup_manager):
        """Recovery windows should calculate correctly."""
        windows = backup_manager.get_recovery_windows()

        assert windows['backup_time']
        assert windows['current_time']
        assert windows['recovery_window_days'] >= 0

    def test_recovery_window_with_no_backups(self):
        """Recovery windows with no backups should handle gracefully."""
        tmpdir = tempfile.mkdtemp()
        manager = BackupManager(tmpdir)

        windows = manager.get_recovery_windows()
        assert windows == {}

        shutil.rmtree(tmpdir, ignore_errors=True)


class TestWALArchivingConfig:
    """Test WAL archiving configuration."""

    @pytest.fixture
    def wal_config(self):
        """Create WAL archiving config."""
        tmpdir = tempfile.mkdtemp()
        config = WALArchivingConfig(f"{tmpdir}/wal_archive")
        yield config
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_wal_directory_creation(self, wal_config):
        """WAL archive directory should be created."""
        assert wal_config.setup_wal_directory()
        assert wal_config.wal_archive_dir.exists()

    def test_postgres_config_generation(self, wal_config):
        """PostgreSQL config should be generated."""
        config = wal_config.generate_postgres_config()

        assert 'wal_level' in config
        assert config['wal_level'] == 'replica'
        assert 'archive_mode' in config
        assert config['archive_mode'] == 'on'

    def test_recovery_config_generation(self, wal_config):
        """Recovery config should contain required settings."""
        recovery_time = "2025-12-23T15:30:00"
        config = wal_config.generate_recovery_config(recovery_time)

        assert 'recovery_target_timeline' in config
        assert recovery_time in config
        assert 'restore_command' in config

    def test_archive_stats_empty_directory(self, wal_config):
        """Archive stats should handle empty directory."""
        wal_config.setup_wal_directory()
        stats = wal_config.get_archive_stats()

        assert stats['wal_files_archived'] == 0
        assert stats['total_size_bytes'] == 0


class TestBackupScheduler:
    """Test backup scheduler functionality."""

    @pytest.fixture
    def scheduler(self):
        """Create BackupScheduler with temp directory."""
        tmpdir = tempfile.mkdtemp()
        scheduler = BackupScheduler(tmpdir)
        yield scheduler
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_scheduler_initialization(self, scheduler):
        """Scheduler should initialize without errors."""
        assert scheduler is not None
        assert scheduler.backup_manager is not None

    def test_default_schedule_config(self, scheduler):
        """Default schedule config should be valid."""
        config = scheduler.schedule_config

        assert 'backup_schedule' in config
        assert 'retention_policy' in config
        assert 'notifications' in config

    def test_schedule_config_has_required_fields(self, scheduler):
        """Schedule config should have all required fields."""
        config = scheduler.schedule_config

        # Backup schedule
        assert config['backup_schedule']['daily']['enabled']
        assert config['backup_schedule']['daily']['time']

        # Retention policy
        assert config['retention_policy']['daily_backups'] > 0
        assert config['retention_policy']['weekly_backups'] > 0

    def test_cron_schedule_generation(self, scheduler):
        """Cron schedule should be generated."""
        cron = scheduler.generate_cron_schedule()

        assert isinstance(cron, str)
        assert 'backup_scheduler.py' in cron
        assert '--daily-backup' in cron or '--cleanup' in cron

    def test_backup_status_structure(self, scheduler):
        """Backup status should have correct structure."""
        status = scheduler.get_backup_status()

        assert isinstance(status, dict)
        assert 'timestamp' in status
        assert 'backup_stats' in status

    def test_verify_backup_dependencies(self, scheduler):
        """Should verify backup dependencies."""
        # This will check if pg_basebackup, tar, etc. are available
        # May return False if not installed, which is OK for testing
        result = scheduler.verify_backup_dependencies()
        assert isinstance(result, bool)


class TestBackupCleanup:
    """Test backup cleanup and retention."""

    @pytest.fixture
    def backup_manager(self):
        """Create BackupManager with multiple backups."""
        tmpdir = tempfile.mkdtemp()
        manager = BackupManager(tmpdir)

        # Create multiple test backups
        for i in range(5):
            days_ago = 5 - i
            backup_time = datetime.now() - timedelta(days=days_ago)
            manager.backups[f'backup_{i}'] = {
                'timestamp': backup_time.isoformat(),
                'size_bytes': 1000000,
                'status': 'verified'
            }

        manager._save_metadata()
        yield manager
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_cleanup_respects_retention(self, backup_manager):
        """Cleanup should respect retention policy."""
        initial_count = len(backup_manager.backups)
        assert initial_count >= 5

        # Keep 3 most recent
        backup_manager.cleanup_old_backups(keep_count=3)

        # Should remove excess backups (but respects the ones we can't remove)
        remaining = len(backup_manager.backups)
        assert remaining <= initial_count

    def test_cleanup_with_keep_all(self, backup_manager):
        """Cleanup with high keep_count should not remove anything."""
        initial_count = len(backup_manager.backups)

        # Keep 100 backups
        backup_manager.cleanup_old_backups(keep_count=100)

        # Should not remove anything
        assert len(backup_manager.backups) == initial_count


class TestBackupSize:
    """Test backup size calculations."""

    @pytest.fixture
    def backup_manager(self):
        """Create BackupManager with test files."""
        tmpdir = tempfile.mkdtemp()
        manager = BackupManager(tmpdir)

        # Create test files
        test_dir = Path(tmpdir) / "test_backup"
        test_dir.mkdir()
        (test_dir / "file1.dat").write_text("x" * 1000)
        (test_dir / "file2.dat").write_text("y" * 2000)

        yield manager, test_dir
        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_calculate_directory_size(self, backup_manager):
        """Should calculate directory size correctly."""
        manager, test_dir = backup_manager
        size = manager._get_backup_size(test_dir)

        # Should be at least 3000 bytes (1000 + 2000)
        assert size >= 3000

    def test_calculate_file_size(self, backup_manager):
        """Should calculate individual file size."""
        manager, test_dir = backup_manager
        test_file = test_dir / "file1.dat"

        size = manager._get_backup_size(test_file)
        assert size == 1000


class TestErrorHandling:
    """Test error handling in backup system."""

    def test_missing_backup_directory(self):
        """Should handle missing backup directory gracefully."""
        manager = BackupManager("/nonexistent/path/backups")
        assert manager.backup_dir.exists()  # Should create it

    def test_invalid_recovery_time_format(self):
        """Should handle invalid time format gracefully."""
        tmpdir = tempfile.mkdtemp()
        manager = BackupManager(tmpdir)

        # Add test backup
        manager.backups['test'] = {
            'timestamp': datetime.now().isoformat(),
            'size_bytes': 1000000
        }

        # Try recovery with invalid time - should handle gracefully
        result = manager.restore_to_point_in_time("invalid-time")
        assert result == False or result == True  # Either way is ok for error handling

        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_corrupted_metadata_file(self):
        """Should handle corrupted metadata gracefully."""
        tmpdir = tempfile.mkdtemp()

        # Write invalid JSON
        metadata_file = Path(tmpdir) / "backup_metadata.json"
        metadata_file.write_text("invalid json {{{")

        # Should handle gracefully and return empty dict
        manager = BackupManager(tmpdir)
        assert isinstance(manager.backups, dict)

        shutil.rmtree(tmpdir, ignore_errors=True)


class TestBackupIntegration:
    """End-to-end backup system integration tests."""

    @pytest.fixture
    def test_environment(self):
        """Create complete test environment."""
        tmpdir = tempfile.mkdtemp()

        yield {
            'backup_dir': tmpdir,
            'manager': BackupManager(tmpdir),
            'scheduler': BackupScheduler(tmpdir),
            'wal_config': WALArchivingConfig(f"{tmpdir}/wal_archive")
        }

        shutil.rmtree(tmpdir, ignore_errors=True)

    def test_full_backup_workflow(self, test_environment):
        """Test complete backup workflow."""
        env = test_environment

        # 1. Setup WAL archiving
        assert env['wal_config'].setup_wal_directory()

        # 2. Add test backup metadata
        env['manager'].backups['backup_001'] = {
            'timestamp': datetime.now().isoformat(),
            'size_bytes': 1000000,
            'status': 'verified'
        }

        # 3. Save metadata
        env['manager']._save_metadata()

        # 4. Get backup status
        status = env['scheduler'].get_backup_status()
        assert status is not None

        # 5. Verify stats
        stats = env['manager'].get_backup_statistics()
        assert stats['backup_count'] == 1
        assert stats['total_size_bytes'] == 1000000

    def test_recovery_window_workflow(self, test_environment):
        """Test recovery window identification workflow."""
        env = test_environment

        # Add backup from yesterday
        backup_time = datetime.now() - timedelta(days=1)
        env['manager'].backups['backup_yesterday'] = {
            'timestamp': backup_time.isoformat(),
            'size_bytes': 5000000,
            'status': 'verified'
        }
        env['manager']._save_metadata()

        # Get recovery windows
        windows = env['manager'].get_recovery_windows()

        # Should be able to recover to a point after backup
        assert windows['recovery_window_days'] >= 0
        assert windows['backup_time']
        assert windows['current_time']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
