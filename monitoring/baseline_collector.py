#!/usr/bin/env python3
"""
Collect performance baseline metrics for tracking optimization progress.

Captures initial performance metrics to use as baseline for comparison
after optimizations are applied.

Usage:
    python monitoring/baseline_collector.py --create
    python monitoring/baseline_collector.py --compare
    python monitoring/baseline_collector.py --show
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
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

try:
    import psycopg2
except ImportError:
    logger.error("❌ psycopg2 not installed")
    sys.exit(1)


class BaselineCollector:
    """Collects and manages performance baseline metrics."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize baseline collector."""
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://yukyu_user:change_me@localhost:5432/yukyu'
        )
        self.baseline_file = Path(__file__).parent.parent / 'monitoring' / 'baselines.json'
        self.baselines = self._load_baselines()

    def _load_baselines(self) -> Dict[str, Any]:
        """Load existing baselines from file."""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"⚠️  Could not load baselines: {e}")
                return {}
        return {}

    def _save_baselines(self):
        """Save baselines to file."""
        try:
            self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.baseline_file, 'w') as f:
                json.dump(self.baselines, f, indent=2, default=str)
            logger.info(f"✅ Baselines saved to {self.baseline_file}")
        except Exception as e:
            logger.error(f"❌ Could not save baselines: {e}")

    def connect(self) -> psycopg2.connection:
        """Create PostgreSQL connection."""
        try:
            return psycopg2.connect(self.database_url)
        except psycopg2.Error as e:
            logger.error(f"❌ Connection failed: {e}")
            raise

    def collect_baseline(self) -> bool:
        """Collect all baseline metrics."""
        logger.info("📊 Collecting performance baseline...\n")

        try:
            conn = self.connect()
            timestamp = datetime.now().isoformat()

            baseline = {
                'timestamp': timestamp,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'metrics': {}
            }

            # Collect database size
            cursor = conn.cursor()
            cursor.execute("SELECT pg_database_size(current_database())")
            db_size = cursor.fetchone()[0]
            baseline['metrics']['database_size_mb'] = db_size / 1024 / 1024

            logger.info(f"  Database size: {baseline['metrics']['database_size_mb']:.2f} MB")

            # Collect table sizes and row counts
            cursor.execute("""
                SELECT
                    tablename,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_size,
                    n_live_tup
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            table_metrics = {}
            for row in cursor.fetchall():
                tablename, total_size, live_rows = row
                table_metrics[tablename] = {
                    'size_mb': total_size / 1024 / 1024,
                    'rows': live_rows
                }
                logger.info(f"  {tablename}: {live_rows} rows, {total_size / 1024 / 1024:.2f} MB")

            baseline['metrics']['tables'] = table_metrics

            # Collect index statistics
            cursor.execute("""
                SELECT COUNT(*) FROM pg_stat_user_indexes
            """)
            baseline['metrics']['index_count'] = cursor.fetchone()[0]

            logger.info(f"  Indexes: {baseline['metrics']['index_count']}")

            # Collect cache hit ratio
            cursor.execute("""
                SELECT
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100
                FROM pg_statio_user_tables
            """)

            result = cursor.fetchone()[0]
            baseline['metrics']['cache_hit_ratio'] = float(result) if result else 0

            logger.info(f"  Cache hit ratio: {baseline['metrics']['cache_hit_ratio']:.2f}%")

            # Collect connections
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            baseline['metrics']['connection_count'] = cursor.fetchone()[0]

            logger.info(f"  Connections: {baseline['metrics']['connection_count']}")

            conn.close()

            # Save as current baseline
            self.baselines['current'] = baseline
            self.baselines['history'] = self.baselines.get('history', [])
            self.baselines['history'].append(baseline)

            # Keep only last 10 baselines
            self.baselines['history'] = self.baselines['history'][-10:]

            self._save_baselines()
            return True

        except Exception as e:
            logger.error(f"❌ Baseline collection failed: {e}")
            return False

    def compare_baselines(self) -> bool:
        """Compare current metrics with baseline."""
        if 'current' not in self.baselines or not self.baselines['current']:
            logger.error("❌ No baseline found. Create one with --create")
            return False

        logger.info("📊 Comparing metrics with baseline...\n")

        try:
            conn = self.connect()
            cursor = conn.cursor()

            baseline = self.baselines['current']
            baseline_date = baseline.get('date', 'unknown')
            logger.info(f"  Baseline: {baseline_date}\n")

            # Compare database size
            cursor.execute("SELECT pg_database_size(current_database())")
            current_db_size = cursor.fetchone()[0] / 1024 / 1024
            baseline_db_size = baseline['metrics']['database_size_mb']

            size_change = current_db_size - baseline_db_size
            size_pct = (size_change / baseline_db_size * 100) if baseline_db_size > 0 else 0

            logger.info(f"Database Size:")
            logger.info(f"  Baseline: {baseline_db_size:.2f} MB")
            logger.info(f"  Current:  {current_db_size:.2f} MB")
            logger.info(f"  Change:   {size_change:+.2f} MB ({size_pct:+.1f}%)")

            if size_pct > 20:
                logger.warning(f"  ⚠️  Significant size increase - check for bloat")

            # Compare table statistics
            logger.info(f"\nTable Statistics:")
            cursor.execute("""
                SELECT
                    tablename,
                    n_live_tup
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            for row in cursor.fetchall():
                tablename, current_rows = row
                baseline_rows = baseline['metrics']['tables'].get(tablename, {}).get('rows', 0)
                row_change = current_rows - baseline_rows

                if row_change != 0:
                    logger.info(f"  {tablename}: {current_rows} rows (baseline: {baseline_rows}, "
                               f"change: {row_change:+d})")

            # Compare cache hit ratio
            cursor.execute("""
                SELECT
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100
                FROM pg_statio_user_tables
            """)

            current_cache = float(cursor.fetchone()[0]) if cursor.fetchone()[0] else 0
            baseline_cache = baseline['metrics']['cache_hit_ratio']

            logger.info(f"\nCache Hit Ratio:")
            logger.info(f"  Baseline: {baseline_cache:.2f}%")
            logger.info(f"  Current:  {current_cache:.2f}%")
            logger.info(f"  Change:   {current_cache - baseline_cache:+.2f}%")

            if current_cache < baseline_cache * 0.9:
                logger.warning(f"  ⚠️  Significant cache degradation")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ Comparison failed: {e}")
            return False

    def show_baselines(self) -> bool:
        """Show all collected baselines."""
        if not self.baselines:
            logger.info("ℹ️  No baselines found")
            return False

        logger.info("📊 Baseline History:\n")

        history = self.baselines.get('history', [])
        for i, baseline in enumerate(history, 1):
            date = baseline.get('date', 'unknown')
            db_size = baseline['metrics'].get('database_size_mb', 0)
            cache_ratio = baseline['metrics'].get('cache_hit_ratio', 0)

            logger.info(f"  {i}. {date}")
            logger.info(f"     DB Size: {db_size:.2f} MB, Cache Hit: {cache_ratio:.2f}%")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect and manage performance baselines'
    )
    parser.add_argument(
        '--create',
        action='store_true',
        help='Create new baseline'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare current metrics with baseline'
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Show baseline history'
    )

    args = parser.parse_args()

    collector = BaselineCollector()

    if args.create:
        if collector.collect_baseline():
            return 0
        else:
            return 1
    elif args.compare:
        if collector.compare_baselines():
            return 0
        else:
            return 1
    elif args.show:
        if collector.show_baselines():
            return 0
        else:
            return 1
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
