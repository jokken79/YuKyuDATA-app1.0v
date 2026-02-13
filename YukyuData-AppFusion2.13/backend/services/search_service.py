#!/usr/bin/env python3
"""
Full-text search service for YuKyuDATA.

Provides fast full-text search across employee tables using PostgreSQL tsvector
and GIN indexes. Supports searching by employee name, location, status, and more.

Usage:
    from services.search_service import SearchService

    search = SearchService()
    results = search.search_employees("Tanaka", limit=10)
    results = search.search_genzai("factory", limit=20)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Only import database if PostgreSQL is available
try:
    import database
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    logger.warning("⚠️  Database module not available")


class SearchService:
    """Provides full-text search functionality for employee records."""

    # Whitelist of allowed tables for search queries (SQL Injection prevention)
    ALLOWED_TABLES = frozenset({'employees', 'genzai', 'ukeoi', 'staff'})

    def __init__(self):
        """Initialize search service."""
        self.use_postgresql = os.getenv('DATABASE_TYPE', 'sqlite').lower() == 'postgresql'

        if not self.use_postgresql:
            logger.warning("⚠️  Full-text search requires PostgreSQL")

    def _execute_search(
        self,
        table: str,
        columns: List[str],
        query: str,
        limit: int,
        offset: int,
        order_by: str = "relevance DESC"
    ) -> List[Dict[str, Any]]:
        """
        Generic search execution method (DRY helper).

        Args:
            table: Table name (must be in ALLOWED_TABLES)
            columns: List of column names to select
            query: Search query string
            limit: Maximum results
            offset: Pagination offset
            order_by: ORDER BY clause

        Returns:
            List of matching records as dictionaries
        """
        if table not in self.ALLOWED_TABLES:
            logger.warning(f"⚠️  Rejected invalid table: {table}")
            return []

        if not self.use_postgresql or not HAS_DATABASE:
            return []

        try:
            with database.get_db() as conn:
                cursor = conn.cursor()

                # Build column list for SELECT
                select_cols = ', '.join(columns)

                cursor.execute(f"""
                    SELECT {select_cols},
                           ts_rank(search_vector, query) as relevance
                    FROM {table},
                         plainto_tsquery('english', %s) query
                    WHERE search_vector @@ query
                    ORDER BY {order_by}
                    LIMIT %s OFFSET %s
                """, (query, limit, offset))

                result_columns = columns + ['relevance']
                results = [dict(zip(result_columns, row)) for row in cursor.fetchall()]

                logger.info(f"✅ Found {len(results)} {table} matching '{query}'")
                return results

        except Exception as e:
            logger.error(f"❌ {table} search failed: {e}")
            return []

    def search_employees(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search employees by name or dispatch location.

        Args:
            query: Search query string
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of matching employee records with relevance ranking
        """
        if not self.use_postgresql or not HAS_DATABASE:
            logger.warning("⚠️  Full-text search requires PostgreSQL")
            return []

        try:
            with database.get_db() as conn:
                cursor = conn.cursor()

                # Use plainto_tsquery for simple phrase search
                # Include kana from genzai/ukeoi tables
                cursor.execute("""
                    SELECT
                        e.id,
                        e.employee_num,
                        e.name,
                        COALESCE(g.kana, u.kana, '') as kana,
                        e.haken,
                        e.granted,
                        e.used,
                        e.balance,
                        e.year,
                        ts_rank(e.search_vector, query) as relevance
                    FROM employees e
                    LEFT JOIN genzai g ON e.employee_num = g.employee_num
                    LEFT JOIN ukeoi u ON e.employee_num = u.employee_num,
                         plainto_tsquery('english', %s) query
                    WHERE e.search_vector @@ query
                    ORDER BY relevance DESC, e.year DESC
                    LIMIT %s OFFSET %s
                """, (query, limit, offset))

                columns = [
                    'id', 'employee_num', 'name', 'kana', 'haken',
                    'granted', 'used', 'balance', 'year', 'relevance'
                ]

                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                logger.info(f"✅ Found {len(results)} employees matching '{query}'")
                return results

        except Exception as e:
            logger.error(f"❌ Employee search failed: {e}")
            return []

    def search_genzai(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search dispatch employees (Genzai).

        Args:
            query: Search query string (name, dispatch location, department)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of matching genzai records with relevance ranking
        """
        if not self.use_postgresql or not HAS_DATABASE:
            return []

        try:
            with database.get_db() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        id,
                        employee_num,
                        name,
                        kana,
                        dispatch_name,
                        department,
                        status,
                        hire_date,
                        ts_rank(search_vector, query) as relevance
                    FROM genzai,
                         plainto_tsquery('english', %s) query
                    WHERE search_vector @@ query
                    ORDER BY relevance DESC, hire_date DESC
                    LIMIT %s OFFSET %s
                """, (query, limit, offset))

                columns = [
                    'id', 'employee_num', 'name', 'kana', 'dispatch_name',
                    'department', 'status', 'hire_date', 'relevance'
                ]

                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                logger.info(f"✅ Found {len(results)} genzai matching '{query}'")
                return results

        except Exception as e:
            logger.error(f"❌ Genzai search failed: {e}")
            return []

    def search_ukeoi(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search contract employees (Ukeoi).

        Args:
            query: Search query string (name, contract business)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of matching ukeoi records with relevance ranking
        """
        if not self.use_postgresql or not HAS_DATABASE:
            return []

        try:
            with database.get_db() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        id,
                        employee_num,
                        name,
                        kana,
                        contract_business,
                        status,
                        hire_date,
                        ts_rank(search_vector, query) as relevance
                    FROM ukeoi,
                         plainto_tsquery('english', %s) query
                    WHERE search_vector @@ query
                    ORDER BY relevance DESC, hire_date DESC
                    LIMIT %s OFFSET %s
                """, (query, limit, offset))

                columns = [
                    'id', 'employee_num', 'name', 'kana', 'contract_business',
                    'status', 'hire_date', 'relevance'
                ]

                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                logger.info(f"✅ Found {len(results)} ukeoi matching '{query}'")
                return results

        except Exception as e:
            logger.error(f"❌ Ukeoi search failed: {e}")
            return []

    def search_staff(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Search staff members.

        Args:
            query: Search query string (name, office)
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of matching staff records with relevance ranking
        """
        if not self.use_postgresql or not HAS_DATABASE:
            return []

        try:
            with database.get_db() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT
                        id,
                        employee_num,
                        name,
                        kana,
                        office,
                        status,
                        hire_date,
                        ts_rank(search_vector, query) as relevance
                    FROM staff,
                         plainto_tsquery('english', %s) query
                    WHERE search_vector @@ query
                    ORDER BY relevance DESC, hire_date DESC
                    LIMIT %s OFFSET %s
                """, (query, limit, offset))

                columns = [
                    'id', 'employee_num', 'name', 'kana', 'office',
                    'status', 'hire_date', 'relevance'
                ]

                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                logger.info(f"✅ Found {len(results)} staff matching '{query}'")
                return results

        except Exception as e:
            logger.error(f"❌ Staff search failed: {e}")
            return []

    def get_search_count(self, table: str, query: str) -> int:
        """Get total count of matching records (for pagination).

        Args:
            table: Table name (must be in ALLOWED_TABLES whitelist)
            query: Search query string

        Returns:
            Count of matching records, or 0 if invalid table or error
        """
        # SQL Injection prevention: validate table name against whitelist
        if table not in self.ALLOWED_TABLES:
            logger.warning(f"⚠️  Rejected invalid table name: {table}")
            return 0

        if not self.use_postgresql or not HAS_DATABASE:
            return 0

        try:
            with database.get_db() as conn:
                cursor = conn.cursor()

                # Table name is now safe (validated against whitelist)
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM {table},
                         plainto_tsquery('english', %s) query
                    WHERE search_vector @@ query
                """, (query,))

                return cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"❌ Count query failed for {table}: {e}")
            return 0

    def search_all_employees(
        self,
        query: str,
        limit: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all employee types (employees, genzai, ukeoi, staff).

        Args:
            query: Search query string
            limit: Maximum results per table

        Returns:
            Dictionary with results grouped by table
        """
        logger.info(f"\n🔍 Searching across all employee types for: '{query}'")

        results = {
            'employees': self.search_employees(query, limit=limit),
            'genzai': self.search_genzai(query, limit=limit),
            'ukeoi': self.search_ukeoi(query, limit=limit),
            'staff': self.search_staff(query, limit=limit)
        }

        total = sum(len(v) for v in results.values())
        logger.info(f"✅ Total results: {total} across {sum(1 for v in results.values() if v)} tables")

        return results


def test_search():
    """Test search functionality."""
    logger.info("🧪 Testing full-text search...\n")

    search = SearchService()

    if not search.use_postgresql:
        logger.warning("⚠️  PostgreSQL not configured for testing")
        return

    # Test searches
    test_queries = [
        "Tanaka",  # Common Japanese name
        "factory",  # Dispatch location
        "2025",  # Year
        "marketing",  # Department
    ]

    for query in test_queries:
        logger.info(f"\n📍 Searching for: '{query}'")

        results = search.search_all_employees(query, limit=5)

        for table, records in results.items():
            if records:
                logger.info(f"  {table}: {len(records)} results")
                for record in records[:2]:  # Show first 2
                    if 'name' in record:
                        logger.info(f"    - {record.get('name')} (relevance: {record.get('relevance', 'N/A')})")

    logger.info("\n✅ Search test completed")


if __name__ == '__main__':
    test_search()
