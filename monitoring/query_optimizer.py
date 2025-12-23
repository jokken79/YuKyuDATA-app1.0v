#!/usr/bin/env python3
"""
Query optimization analyzer for PostgreSQL.

Analyzes slow queries, suggests indexes, and provides optimization recommendations.

Usage:
    python monitoring/query_optimizer.py
    python monitoring/query_optimizer.py --analyze-table employees
    python monitoring/query_optimizer.py --suggest-indexes
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import argparse
import logging
import json

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


class QueryOptimizer:
    """Analyzes and optimizes PostgreSQL queries."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize query optimizer."""
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://yukyu_user:change_me@localhost:5432/yukyu'
        )
        self.recommendations = []

    def connect(self) -> psycopg2.connection:
        """Create PostgreSQL connection."""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def analyze_query(self, conn: psycopg2.connection, query: str) -> Dict[str, Any]:
        """Analyze a single query and provide optimization suggestions."""
        logger.info(f"\n📋 Analyzing query: {query[:60]}...")

        cursor = conn.cursor()
        analysis = {
            'query': query,
            'plan': None,
            'seq_scans': False,
            'suggestions': []
        }

        try:
            # Get query plan
            cursor.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {query}")
            plan_json = cursor.fetchone()[0]

            if isinstance(plan_json, str):
                plan = json.loads(plan_json)
            else:
                plan = plan_json

            analysis['plan'] = plan

            # Analyze plan for optimization opportunities
            self._analyze_plan(plan[0], analysis)

            return analysis

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not analyze query: {e}")
            return analysis

    def _analyze_plan(self, plan_node: Dict[str, Any], analysis: Dict[str, Any]):
        """Recursively analyze query plan nodes."""
        node_type = plan_node.get('Node Type', '')

        # Check for sequential scans (usually inefficient for large tables)
        if 'Seq Scan' in node_type:
            analysis['seq_scans'] = True

            table = plan_node.get('Relation Name')
            if table:
                logger.warning(f"  ⚠️  Sequential scan on {table}")
                analysis['suggestions'].append(f"Consider adding index on {table}")

        # Check for full table scans with filter
        if 'Seq Scan' in node_type and 'Filter' in plan_node:
            analysis['suggestions'].append("Sequential scan with filter - index could improve performance")

        # Recursively check child plans
        if 'Plans' in plan_node:
            for child_plan in plan_node['Plans']:
                self._analyze_plan(child_plan, analysis)

    def get_table_scan_queries(self, conn: psycopg2.connection) -> List[Dict[str, Any]]:
        """Find queries that use sequential scans and could benefit from indexes."""
        logger.info("\n🔍 Finding queries with sequential scans...")

        cursor = conn.cursor()
        seq_scan_queries = []

        try:
            # Get queries with sequential scans
            cursor.execute("""
                SELECT
                    query,
                    seq_scan_count,
                    calls,
                    mean_exec_time
                FROM (
                    SELECT
                        query,
                        (SELECT SUM(seq_scan) FROM pg_stat_user_tables) as seq_scan_count,
                        calls,
                        mean_exec_time
                    FROM pg_stat_statements
                    ORDER BY calls DESC
                    LIMIT 20
                ) t
                WHERE seq_scan_count > 0
                ORDER BY mean_exec_time DESC
            """)

            for row in cursor.fetchall():
                query, seq_scans, calls, mean_time = row

                seq_scan_queries.append({
                    'query': query[:100],
                    'full_query': query,
                    'seq_scans': seq_scans,
                    'calls': calls,
                    'mean_time': mean_time
                })

                logger.info(f"  {query[:70]}...")
                logger.info(f"    Seq Scans: {seq_scans}, Calls: {calls}, Mean: {mean_time:.2f}ms")

            return seq_scan_queries

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not retrieve seq scan queries: {e}")
            return []

    def suggest_missing_indexes(self, conn: psycopg2.connection) -> List[str]:
        """Suggest indexes based on query patterns."""
        logger.info("\n💡 Suggesting missing indexes...")

        cursor = conn.cursor()
        suggestions = []

        try:
            # Analyze table structure and suggest indexes
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    avg_width,
                    n_distinct
                FROM pg_stat_user_tables
                JOIN pg_stat_user_columns USING (schemaname, tablename)
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
            """)

            current_table = None
            table_columns = {}

            for row in cursor.fetchall():
                schemaname, tablename, attname, avg_width, n_distinct = row

                if tablename != current_table:
                    if current_table and table_columns:
                        suggestions.extend(self._analyze_table_for_indexes(
                            current_table, table_columns, conn
                        ))
                    current_table = tablename
                    table_columns = {}

                table_columns[attname] = {
                    'avg_width': avg_width,
                    'n_distinct': n_distinct or 0
                }

            # Analyze final table
            if current_table and table_columns:
                suggestions.extend(self._analyze_table_for_indexes(
                    current_table, table_columns, conn
                ))

            return suggestions

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not suggest indexes: {e}")
            return []

    def _analyze_table_for_indexes(
        self,
        table_name: str,
        columns: Dict[str, Dict[str, Any]],
        conn: psycopg2.connection
    ) -> List[str]:
        """Analyze a table and suggest specific indexes."""
        suggestions = []

        # Suggest indexes for commonly filtered columns
        important_columns = ['employee_num', 'status', 'year', 'date', 'use_date']

        for col_name in important_columns:
            if col_name in columns:
                # Check if index already exists
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM pg_indexes
                    WHERE tablename = %s AND indexdef LIKE %s
                """, (table_name, f'%{col_name}%'))

                if cursor.fetchone()[0] == 0:
                    suggestion = f"CREATE INDEX idx_{table_name}_{col_name} ON {table_name}({col_name});"
                    logger.info(f"  💡 Suggested for {table_name}.{col_name}:")
                    logger.info(f"     {suggestion}")
                    suggestions.append(suggestion)

        return suggestions

    def analyze_table_structure(
        self,
        conn: psycopg2.connection,
        table_name: str
    ) -> Dict[str, Any]:
        """Analyze structure of a specific table."""
        logger.info(f"\n📊 Analyzing table structure for {table_name}...")

        cursor = conn.cursor()

        try:
            # Get table info
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_size,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum
                FROM pg_stat_user_tables
                WHERE tablename = %s
            """, (table_name,))

            table_info = cursor.fetchone()

            if not table_info:
                logger.warning(f"  ⚠️  Table {table_name} not found")
                return {}

            schema, table, total_size, live_rows, dead_rows, last_vac, last_avac = table_info

            analysis = {
                'table': table_name,
                'size_mb': total_size / 1024 / 1024,
                'live_rows': live_rows,
                'dead_rows': dead_rows,
                'last_vacuum': last_vac,
                'last_autovacuum': last_avac,
                'bloat_percentage': (dead_rows * 100.0 / (live_rows + dead_rows)) if (live_rows + dead_rows) > 0 else 0,
                'columns': [],
                'indexes': []
            }

            # Get columns
            cursor.execute("""
                SELECT
                    attname,
                    typname,
                    attnotnull,
                    atthasdef
                FROM pg_stat_user_columns
                JOIN pg_attribute USING (attnum)
                JOIN pg_type ON pg_attribute.atttypid = pg_type.oid
                WHERE schemaname = %s AND tablename = %s
                ORDER BY attnum
            """, (schema, table_name))

            for col in cursor.fetchall():
                attname, typname, notnull, hasdef = col
                analysis['columns'].append({
                    'name': attname,
                    'type': typname,
                    'not_null': notnull,
                    'has_default': hasdef
                })

            # Get indexes
            cursor.execute("""
                SELECT
                    indexname,
                    indexdef,
                    idx_scan
                FROM pg_stat_user_indexes
                WHERE tablename = %s
                ORDER BY idx_scan DESC
            """, (table_name,))

            for idx in cursor.fetchall():
                indexname, indexdef, idx_scan = idx
                analysis['indexes'].append({
                    'name': indexname,
                    'scans': idx_scan,
                    'definition': indexdef
                })

            # Print summary
            logger.info(f"  Size: {analysis['size_mb']:.2f} MB")
            logger.info(f"  Rows: {live_rows} (dead: {dead_rows}, bloat: {analysis['bloat_percentage']:.1f}%)")
            logger.info(f"  Columns: {len(analysis['columns'])}")
            logger.info(f"  Indexes: {len(analysis['indexes'])}")

            return analysis

        except psycopg2.Error as e:
            logger.warning(f"  ⚠️  Could not analyze table: {e}")
            return {}

    def generate_optimization_report(self) -> bool:
        """Generate comprehensive optimization report."""
        logger.info("📈 Generating query optimization report...\n")

        try:
            conn = self.connect()

            # 1. Analyze slow queries
            self.get_table_scan_queries(conn)

            # 2. Suggest missing indexes
            suggestions = self.suggest_missing_indexes(conn)

            if suggestions:
                logger.info("\n📋 Suggested indexes to create:")
                for i, suggestion in enumerate(suggestions, 1):
                    logger.info(f"  {i}. {suggestion}")

            # 3. Analyze critical tables
            critical_tables = ['employees', 'genzai', 'ukeoi', 'leave_requests']

            for table in critical_tables:
                self.analyze_table_structure(conn, table)

            conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze and optimize PostgreSQL queries'
    )
    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection URL'
    )
    parser.add_argument(
        '--analyze-table',
        help='Analyze specific table structure'
    )
    parser.add_argument(
        '--suggest-indexes',
        action='store_true',
        help='Get index creation suggestions'
    )
    parser.add_argument(
        '--analyze-queries',
        action='store_true',
        help='Analyze slow queries'
    )

    args = parser.parse_args()

    optimizer = QueryOptimizer(args.database_url)

    if args.analyze_table:
        try:
            conn = optimizer.connect()
            optimizer.analyze_table_structure(conn, args.analyze_table)
            conn.close()
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            return 1
    else:
        if optimizer.generate_optimization_report():
            return 0
        else:
            return 1


if __name__ == '__main__':
    sys.exit(main())
