#!/usr/bin/env python3
"""
Performance monitoring and optimization for PostgreSQL.

Collects detailed performance metrics, identifies bottlenecks, and provides
optimization recommendations for the YuKyuDATA application.

Usage:
    python monitoring/performance_monitor.py
    python monitoring/performance_monitor.py --detailed
    python monitoring/performance_monitor.py --reset-stats
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
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
    logger.error("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


class PerformanceMonitor:
    """Monitors and optimizes PostgreSQL performance."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize performance monitor.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://yukyu_user:change_me@localhost:5432/yukyu'
        )
        self.start_time = None
        self.end_time = None
        self.metrics = {}

    def connect(self) -> psycopg2.connection:
        """Create PostgreSQL connection."""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def check_pg_stat_statements(self, conn: psycopg2.connection) -> bool:
        """Check if pg_stat_statements extension is installed."""
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM pg_stat_statements LIMIT 1")
            return True
        except psycopg2.Error:
            logger.warning("⚠️  pg_stat_statements not installed")
            logger.info("   Install with: CREATE EXTENSION pg_stat_statements;")
            return False

    def get_slow_queries(
        self,
        conn: psycopg2.connection,
        threshold_ms: float = 100
    ) -> List[Dict[str, Any]]:
        """Get slow queries from pg_stat_statements."""
        logger.info(f"\n🔍 Analyzing slow queries (threshold: {threshold_ms}ms)...")

        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    stddev_exec_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_exec_time > %s
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """, (threshold_ms,))

            rows = cursor.fetchall()
            slow_queries = []

            for i, row in enumerate(rows, 1):
                query, calls, total, mean, max_time, stddev, result_rows = row

                # Truncate query for display
                query_display = query[:80] + "..." if len(query) > 80 else query

                slow_queries.append({
                    'query': query,
                    'query_display': query_display,
                    'calls': calls,
                    'total_time': total,
                    'mean_time': mean,
                    'max_time': max_time,
                    'stddev': stddev,
                    'rows': result_rows
                })

                logger.info(f"  {i}. {query_display}")
                logger.info(f"     Calls: {calls}, Mean: {mean:.2f}ms, Max: {max_time:.2f}ms")

            return slow_queries

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not retrieve slow queries: {e}")
            return []

    def get_table_stats(self, conn: psycopg2.connection) -> Dict[str, Dict[str, Any]]:
        """Get table statistics and sizes."""
        logger.info("\n📊 Analyzing table statistics...")

        cursor = conn.cursor()
        table_stats = {}

        try:
            # Get table sizes and row counts
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_total_relation_size(schemaname||'.'||tablename) AS total_size,
                    n_live_tup AS live_rows,
                    n_dead_tup AS dead_rows,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    last_vacuum,
                    last_autovacuum
                FROM pg_stat_user_tables
                ORDER BY total_size DESC
            """)

            for row in cursor.fetchall():
                schemaname, tablename, total_size, live_rows, dead_rows, tup_ins, tup_upd, tup_del, last_vac, last_avac = row

                size_mb = total_size / 1024 / 1024

                table_stats[tablename] = {
                    'size_mb': size_mb,
                    'live_rows': live_rows,
                    'dead_rows': dead_rows,
                    'inserts': tup_ins,
                    'updates': tup_upd,
                    'deletes': tup_del,
                    'last_vacuum': last_vac,
                    'last_autovacuum': last_avac
                }

                logger.info(f"  {tablename}:")
                logger.info(f"    Size: {size_mb:.2f} MB, Rows: {live_rows}")
                logger.info(f"    Dead rows: {dead_rows}, Inserts: {tup_ins}, Updates: {tup_upd}, Deletes: {tup_del}")

            self.metrics['table_stats'] = table_stats
            return table_stats

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not retrieve table stats: {e}")
            return {}

    def get_index_stats(self, conn: psycopg2.connection) -> Dict[str, Dict[str, Any]]:
        """Get index statistics and detect unused indexes."""
        logger.info("\n📇 Analyzing index usage...")

        cursor = conn.cursor()
        index_stats = {}

        try:
            # Get index sizes and usage
            cursor.execute("""
                SELECT
                    tablename,
                    indexname,
                    idx_scan,
                    pg_relation_size(indexrelid) AS index_size
                FROM pg_stat_user_indexes
                ORDER BY index_size DESC
            """)

            used_count = 0
            unused_count = 0

            for row in cursor.fetchall():
                tablename, indexname, idx_scan, index_size = row

                size_mb = index_size / 1024 / 1024

                index_stats[indexname] = {
                    'table': tablename,
                    'scans': idx_scan,
                    'size_mb': size_mb
                }

                if idx_scan == 0:
                    logger.warning(f"  ⚠️  UNUSED: {indexname} on {tablename} ({size_mb:.2f} MB)")
                    unused_count += 1
                else:
                    logger.info(f"  ✅ {indexname}: {idx_scan} scans ({size_mb:.2f} MB)")
                    used_count += 1

            logger.info(f"\n  Summary: {used_count} used, {unused_count} unused indexes")
            self.metrics['index_stats'] = index_stats

            return index_stats

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not retrieve index stats: {e}")
            return {}

    def get_cache_hit_ratio(self, conn: psycopg2.connection) -> float:
        """Get database cache hit ratio."""
        logger.info("\n💾 Checking cache hit ratio...")

        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
                FROM pg_statio_user_tables
            """)

            result = cursor.fetchone()

            if result[0] is None or result[1] is None:
                logger.warning("  ⚠️  No cache statistics available")
                return 0.0

            heap_read, heap_hit, ratio = result

            if ratio is not None:
                ratio = float(ratio) * 100
                logger.info(f"  📈 Cache hit ratio: {ratio:.2f}%")

                if ratio > 95:
                    logger.info("     ✅ Excellent cache performance")
                elif ratio > 80:
                    logger.info("     ✅ Good cache performance")
                else:
                    logger.warning("     ⚠️  Cache hit ratio could be improved")

                self.metrics['cache_hit_ratio'] = ratio
                return ratio
            else:
                logger.warning("  ⚠️  Could not calculate cache ratio")
                return 0.0

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not check cache hit ratio: {e}")
            return 0.0

    def get_connection_stats(self, conn: psycopg2.connection) -> Dict[str, Any]:
        """Get connection pool statistics."""
        logger.info("\n🔌 Checking connection statistics...")

        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    count(*) as total_connections,
                    max(query_start) as oldest_query,
                    state
                FROM pg_stat_activity
                GROUP BY state
                ORDER BY state
            """)

            stats = {
                'total': 0,
                'active': 0,
                'idle': 0,
                'idle_in_transaction': 0,
                'other': 0
            }

            for row in cursor.fetchall():
                count, oldest_query, state = row

                if state == 'active':
                    stats['active'] = count
                    logger.info(f"  🟢 Active: {count}")
                elif state == 'idle':
                    stats['idle'] = count
                    logger.info(f"  🟡 Idle: {count}")
                elif state == 'idle in transaction':
                    stats['idle_in_transaction'] = count
                    logger.warning(f"  🔴 Idle in transaction: {count}")
                else:
                    stats['other'] = count
                    logger.info(f"  {state}: {count}")

                stats['total'] += count

            logger.info(f"  Total connections: {stats['total']}")
            self.metrics['connection_stats'] = stats

            return stats

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not check connections: {e}")
            return {}

    def get_bloat_estimate(self, conn: psycopg2.connection) -> Dict[str, float]:
        """Estimate table and index bloat."""
        logger.info("\n🔍 Analyzing table bloat...")

        cursor = conn.cursor()
        bloat_info = {}

        try:
            # Simple bloat estimate based on dead rows
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as bloat_percentage
                FROM pg_stat_user_tables
                WHERE n_live_tup > 0
                ORDER BY bloat_percentage DESC
            """)

            for row in cursor.fetchall():
                schemaname, tablename, bloat_pct = row

                bloat_info[tablename] = bloat_pct

                if bloat_pct > 20:
                    logger.warning(f"  ⚠️  {tablename}: {bloat_pct:.1f}% bloat (recommend VACUUM)")
                elif bloat_pct > 10:
                    logger.info(f"  ⚠️  {tablename}: {bloat_pct:.1f}% bloat")
                else:
                    logger.info(f"  ✅ {tablename}: {bloat_pct:.1f}% bloat")

            self.metrics['bloat_info'] = bloat_info
            return bloat_info

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not analyze bloat: {e}")
            return {}

    def get_query_plans(self, conn: psycopg2.connection) -> List[Dict[str, Any]]:
        """Analyze query plans for optimization opportunities."""
        logger.info("\n📋 Analyzing query plans for optimization opportunities...")

        cursor = conn.cursor()
        optimization_opportunities = []

        try:
            # Get most called queries
            cursor.execute("""
                SELECT query, calls
                FROM pg_stat_statements
                ORDER BY calls DESC
                LIMIT 5
            """)

            for row in cursor.fetchall():
                query, calls = row

                if 'SELECT' in query.upper():
                    # Analyze the query plan
                    try:
                        cursor.execute(f"EXPLAIN (FORMAT JSON) {query}")
                        plan = cursor.fetchone()

                        if plan:
                            logger.info(f"  Query (called {calls} times):")
                            logger.info(f"    {query[:100]}")
                            optimization_opportunities.append({
                                'query': query,
                                'calls': calls,
                                'plan': plan
                            })

                    except psycopg2.Error:
                        pass

            return optimization_opportunities

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not analyze query plans: {e}")
            return []

    def generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on collected metrics."""
        logger.info("\n💡 Optimization Recommendations:")

        recommendations = []

        # Cache hit ratio recommendation
        cache_ratio = self.metrics.get('cache_hit_ratio', 0)
        if cache_ratio < 80:
            msg = "  🔧 Increase shared_buffers (currently underutilized cache)"
            logger.warning(msg)
            recommendations.append(msg)

        # Bloat recommendation
        bloat_info = self.metrics.get('bloat_info', {})
        for table, bloat_pct in bloat_info.items():
            if bloat_pct > 20:
                msg = f"  🔧 Run VACUUM on {table} ({bloat_pct:.1f}% bloat)"
                logger.warning(msg)
                recommendations.append(msg)

        # Index recommendation
        index_stats = self.metrics.get('index_stats', {})
        unused_count = sum(1 for idx_info in index_stats.values() if idx_info['scans'] == 0)
        if unused_count > 0:
            msg = f"  🔧 Drop {unused_count} unused indexes (saves space and write performance)"
            logger.warning(msg)
            recommendations.append(msg)

        # Slow query recommendation
        logger.info("  🔧 Consider adding indexes for slow queries (see above)")
        recommendations.append("  🔧 Add indexes for slow queries")

        if not recommendations:
            logger.info("  ✅ No major optimization issues found")
            recommendations.append("  ✅ System performing well")

        return recommendations

    def reset_statistics(self, conn: psycopg2.connection) -> bool:
        """Reset pg_stat_statements for fresh baseline."""
        logger.info("\n🔄 Resetting statistics...")

        cursor = conn.cursor()

        try:
            cursor.execute("SELECT pg_stat_statements_reset()")
            logger.info("  ✅ pg_stat_statements reset successfully")
            return True

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not reset statistics: {e}")
            return False

    def run_comprehensive_analysis(self) -> bool:
        """Run comprehensive performance analysis."""
        self.start_time = datetime.now()

        try:
            logger.info("🏥 Starting comprehensive performance analysis...\n")

            conn = self.connect()

            # Check for pg_stat_statements
            if not self.check_pg_stat_statements(conn):
                logger.info("   (Some features will be limited without pg_stat_statements)")

            # Run all analyses
            self.get_slow_queries(conn, threshold_ms=100)
            self.get_table_stats(conn)
            self.get_index_stats(conn)
            self.get_cache_hit_ratio(conn)
            self.get_connection_stats(conn)
            self.get_bloat_estimate(conn)
            self.get_query_plans(conn)

            # Generate recommendations
            recommendations = self.generate_recommendations()

            conn.close()
            self.end_time = datetime.now()
            self.print_summary(recommendations)

            return True

        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}", exc_info=True)
            return False

    def print_summary(self, recommendations: List[str]):
        """Print performance analysis summary."""
        duration = (self.end_time - self.start_time).total_seconds()

        logger.info("\n" + "="*70)
        logger.info("  PERFORMANCE ANALYSIS SUMMARY")
        logger.info("="*70)

        logger.info(f"\n📊 Key Metrics:")
        logger.info(f"  Cache Hit Ratio: {self.metrics.get('cache_hit_ratio', 'N/A')}")

        conn_stats = self.metrics.get('connection_stats', {})
        if conn_stats:
            logger.info(f"  Connections: {conn_stats.get('total', 0)} total "
                       f"({conn_stats.get('active', 0)} active)")

        logger.info(f"\n⏱️  Duration: {duration:.2f} seconds")
        logger.info("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Monitor and optimize PostgreSQL performance'
    )
    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection URL (uses DATABASE_URL env var if not provided)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed analysis'
    )
    parser.add_argument(
        '--reset-stats',
        action='store_true',
        help='Reset pg_stat_statements for fresh baseline'
    )

    args = parser.parse_args()

    monitor = PerformanceMonitor(args.database_url)

    if args.reset_stats:
        try:
            conn = monitor.connect()
            monitor.reset_statistics(conn)
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to reset statistics: {e}")
            return 1
    else:
        if monitor.run_comprehensive_analysis():
            return 0
        else:
            return 1


if __name__ == '__main__':
    sys.exit(main())
