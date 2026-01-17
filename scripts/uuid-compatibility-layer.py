"""
uuid-compatibility-layer.py
Backward Compatibility Layer for UUID Migration

This module provides helper functions to support the gradual migration
from composite-key based lookups to UUID-based lookups.

Usage:
    from scripts.uuid_compatibility import get_employee_uuid, get_employee_by_composite_key

    # Legacy way (will work until Phase 4):
    emp = get_employee_by_composite_key("001", 2025)

    # Modern way (preferred):
    emp = get_employee_by_uuid(emp.id)
"""

import sqlite3
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path
import uuid as uuid_module
from functools import lru_cache
import os

# Cache configuration
UUID_CACHE = {}  # Simple in-memory cache
CACHE_SIZE = 1000  # Maximum cache entries

# Database path - use same logic as database.py
def get_db_path():
    """Get database path."""
    custom_path = os.getenv('DATABASE_PATH')
    if custom_path:
        return custom_path
    if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        return '/tmp/yukyu.db'
    return 'yukyu.db'


class UUIDCompatibility:
    """Helper class for UUID migration compatibility."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db_path()

    def connect(self) -> sqlite3.Connection:
        """Create database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @lru_cache(maxsize=1000)
    def get_employee_uuid(self, employee_num: str, year: int) -> Optional[str]:
        """
        Get UUID for employee given composite key (employee_num, year).

        Args:
            employee_num: Employee number (e.g., "001")
            year: Fiscal year (e.g., 2025)

        Returns:
            UUID string if employee found, None otherwise

        Migration notes:
            - This function is a compatibility layer
            - Will be deprecated in Phase 4
            - Prefer direct UUID usage when possible
        """
        # Check memory cache first
        cache_key = f"{employee_num}_{year}"

        if cache_key in UUID_CACHE:
            return UUID_CACHE[cache_key]

        # Query database
        try:
            conn = self.connect()
            c = conn.cursor()
            c.execute(
                "SELECT id FROM employees WHERE employee_num = ? AND year = ?",
                (employee_num, year)
            )
            result = c.fetchone()
            conn.close()

            if result:
                uuid_val = result[0]
                # Store in cache (with size limit)
                if len(UUID_CACHE) < CACHE_SIZE:
                    UUID_CACHE[cache_key] = uuid_val
                return uuid_val

            return None

        except Exception as e:
            print(f"Error getting employee UUID: {e}")
            return None

    def get_employee_by_composite_key(
        self, employee_num: str, year: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get employee record by composite key (legacy interface).

        Args:
            employee_num: Employee number
            year: Fiscal year

        Returns:
            Employee record as dictionary if found, None otherwise

        Deprecation warning:
            This function provides backward compatibility.
            Migrate to get_employee_by_uuid() when possible.
        """
        try:
            conn = self.connect()
            c = conn.cursor()
            c.execute(
                """
                SELECT * FROM employees
                WHERE employee_num = ? AND year = ?
                """,
                (employee_num, year)
            )
            result = c.fetchone()
            conn.close()

            if result:
                return dict(result)
            return None

        except Exception as e:
            print(f"Error getting employee by composite key: {e}")
            return None

    def get_employee_by_uuid(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Get employee record by UUID (modern interface).

        Args:
            employee_id: Employee UUID

        Returns:
            Employee record as dictionary if found, None otherwise

        This is the preferred way to lookup employees.
        """
        try:
            conn = self.connect()
            c = conn.cursor()
            c.execute(
                "SELECT * FROM employees WHERE id = ?",
                (employee_id,)
            )
            result = c.fetchone()
            conn.close()

            if result:
                return dict(result)
            return None

        except Exception as e:
            print(f"Error getting employee by UUID: {e}")
            return None

    def get_all_employee_ids(self) -> Dict[str, str]:
        """
        Get mapping of composite keys to UUIDs.

        Returns:
            Dictionary with key format "employee_num_year" → "uuid"

        Useful for:
            - Bulk migrations
            - Cache population
            - Audit trails
        """
        mapping = {}

        try:
            conn = self.connect()
            c = conn.cursor()
            c.execute(
                "SELECT employee_num, year, id FROM employees ORDER BY employee_num, year"
            )

            for row in c.fetchall():
                composite_key = f"{row[0]}_{row[1]}"
                mapping[composite_key] = row[2]

            conn.close()
            return mapping

        except Exception as e:
            print(f"Error getting all employee IDs: {e}")
            return {}

    def populate_cache(self) -> int:
        """
        Pre-populate UUID cache from database.

        Returns:
            Number of entries cached

        Use this to improve performance in batch operations.
        """
        mapping = self.get_all_employee_ids()
        for composite_key, uuid_val in mapping.items():
            if len(UUID_CACHE) < CACHE_SIZE:
                UUID_CACHE[composite_key] = uuid_val

        return len(UUID_CACHE)

    def clear_cache(self):
        """Clear UUID cache."""
        UUID_CACHE.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(UUID_CACHE),
            "max_size": CACHE_SIZE,
            "fill_percent": (len(UUID_CACHE) / CACHE_SIZE) * 100,
            "entries": list(UUID_CACHE.keys())[:10]  # Show first 10
        }


# Module-level instance for singleton usage
_instance = None


def get_uuid_compat() -> UUIDCompatibility:
    """Get singleton instance of UUIDCompatibility."""
    global _instance
    if _instance is None:
        _instance = UUIDCompatibility()
    return _instance


# Convenience functions for direct usage
def get_employee_uuid(employee_num: str, year: int) -> Optional[str]:
    """Get UUID for employee (convenience function)."""
    return get_uuid_compat().get_employee_uuid(employee_num, year)


def get_employee_by_composite_key(
    employee_num: str, year: int
) -> Optional[Dict[str, Any]]:
    """Get employee by composite key (convenience function)."""
    return get_uuid_compat().get_employee_by_composite_key(employee_num, year)


def get_employee_by_uuid(employee_id: str) -> Optional[Dict[str, Any]]:
    """Get employee by UUID (convenience function)."""
    return get_uuid_compat().get_employee_by_uuid(employee_id)


def get_all_employee_ids() -> Dict[str, str]:
    """Get all employee ID mappings (convenience function)."""
    return get_uuid_compat().get_all_employee_ids()


def populate_uuid_cache() -> int:
    """Populate UUID cache (convenience function)."""
    return get_uuid_compat().populate_cache()


def clear_uuid_cache():
    """Clear UUID cache (convenience function)."""
    get_uuid_compat().clear_cache()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics (convenience function)."""
    return get_uuid_compat().get_cache_stats()


# Migration logging
class MigrationLogger:
    """Log code paths still using legacy patterns."""

    def __init__(self):
        self.legacy_calls = {}

    def log_legacy_call(self, function_name: str, context: str = ""):
        """Log a legacy function call."""
        if function_name not in self.legacy_calls:
            self.legacy_calls[function_name] = []
        self.legacy_calls[function_name].append({
            "context": context,
            "timestamp": Path('/tmp/migration_log.json').read_text() if Path('/tmp/migration_log.json').exists() else None
        })

    def get_report(self) -> str:
        """Get migration report showing all legacy code paths."""
        report = "Legacy Code Path Migration Report\n"
        report += "=" * 50 + "\n\n"

        for func_name, calls in self.legacy_calls.items():
            report += f"Function: {func_name}\n"
            report += f"  Calls: {len(calls)}\n"
            for call in calls[:3]:  # Show first 3
                report += f"  - {call['context']}\n"
            if len(calls) > 3:
                report += f"  ... and {len(calls) - 3} more\n"
            report += "\n"

        return report


# Global logger instance
_logger = MigrationLogger()


def log_legacy_call(function_name: str, context: str = ""):
    """Log a legacy function call for migration tracking."""
    _logger.log_legacy_call(function_name, context)


def get_migration_report() -> str:
    """Get migration report of legacy code paths."""
    return _logger.get_report()


# Example usage / Testing
if __name__ == "__main__":
    compat = get_uuid_compat()

    print("UUID Compatibility Layer - Test")
    print("=" * 50)
    print()

    # Test getting employee UUID
    print("Test 1: Get employee UUID by composite key")
    uuid = compat.get_employee_uuid("001", 2025)
    if uuid:
        print(f"  Employee 001/2025 → UUID: {uuid}")
    else:
        print("  (No test data)")
    print()

    # Test cache stats
    print("Test 2: Cache statistics")
    stats = compat.get_cache_stats()
    print(f"  Cache size: {stats['size']}/{stats['max_size']}")
    print(f"  Fill: {stats['fill_percent']:.1f}%")
    print()

    # Test populating cache
    print("Test 3: Populate cache from database")
    count = compat.populate_cache()
    print(f"  Cached {count} employee entries")
    print()

    # Test getting all IDs
    print("Test 4: Get all employee ID mappings")
    all_ids = compat.get_all_employee_ids()
    for key, uuid_val in list(all_ids.items())[:3]:
        print(f"  {key} → {uuid_val}")
    if len(all_ids) > 3:
        print(f"  ... and {len(all_ids) - 3} more")
    print()

    print("=" * 50)
    print("All tests completed!")
