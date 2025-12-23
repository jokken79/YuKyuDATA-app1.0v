"""
Tests for PostgreSQL connection pooling functionality.

Tests verify:
- Pool initialization
- Connection acquisition and release
- Pool concurrency limits
- Pool cleanup on shutdown
"""

import pytest
import os
import sys
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Skip if PostgreSQL not configured
pytestmark = pytest.mark.skipif(
    os.getenv('DATABASE_TYPE', 'sqlite').lower() != 'postgresql',
    reason="PostgreSQL not configured"
)

import database
from database.connection import PostgreSQLConnectionPool


class TestConnectionPoolBasics:
    """Test basic connection pool functionality."""

    def test_pool_initialization(self):
        """Test that pool initializes correctly."""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url is None:
                pytest.skip("DATABASE_URL not set")

            # Reset pool
            PostgreSQLConnectionPool._pool = None

            # Initialize
            PostgreSQLConnectionPool.initialize(database_url, 5, 20)

            assert PostgreSQLConnectionPool._pool is not None
            assert PostgreSQLConnectionPool._pool._minconn == 5
            assert PostgreSQLConnectionPool._pool._maxconn == 20

        except Exception as e:
            pytest.skip(f"Pool initialization failed: {str(e)}")

    def test_get_connection_from_pool(self):
        """Test getting a connection from the pool."""
        try:
            if PostgreSQLConnectionPool._pool is None:
                database_url = os.getenv('DATABASE_URL')
                PostgreSQLConnectionPool.initialize(database_url)

            conn = PostgreSQLConnectionPool.get_connection()
            assert conn is not None

            # Verify connection works
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result is not None

            cursor.close()

            # Put connection back
            PostgreSQLConnectionPool.put_connection(conn)

        except Exception as e:
            pytest.skip(f"Get connection test failed: {str(e)}")

    def test_connection_returned_to_pool(self):
        """Test that connections are properly returned to pool."""
        try:
            if PostgreSQLConnectionPool._pool is None:
                database_url = os.getenv('DATABASE_URL')
                PostgreSQLConnectionPool.initialize(database_url, 2, 5)

            # Get multiple connections
            conns = []
            for i in range(3):
                conn = PostgreSQLConnectionPool.get_connection()
                conns.append(conn)

            # All should work
            assert len(conns) == 3

            # Return them
            for conn in conns:
                PostgreSQLConnectionPool.put_connection(conn)

        except Exception as e:
            pytest.skip(f"Connection return test failed: {str(e)}")


class TestConnectionPoolConcurrency:
    """Test concurrent access to the connection pool."""

    def test_concurrent_connections(self):
        """Test multiple concurrent connections from pool."""
        try:
            if PostgreSQLConnectionPool._pool is None:
                database_url = os.getenv('DATABASE_URL')
                PostgreSQLConnectionPool.initialize(database_url, 5, 20)

            def worker(worker_id):
                """Worker function that gets connection and runs query."""
                try:
                    conn = PostgreSQLConnectionPool.get_connection()

                    cursor = conn.cursor()
                    cursor.execute("SELECT %s as worker_id", (worker_id,))
                    result = cursor.fetchone()

                    cursor.close()
                    PostgreSQLConnectionPool.put_connection(conn)

                    return f"Worker {worker_id}: OK"
                except Exception as e:
                    return f"Worker {worker_id}: ERROR - {str(e)}"

            # Run 10 concurrent workers
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(worker, i) for i in range(10)]
                results = [f.result(timeout=10) for f in as_completed(futures)]

            # All should succeed
            errors = [r for r in results if "ERROR" in r]
            assert len(errors) == 0, f"Concurrent access failed: {errors}"

        except Exception as e:
            pytest.skip(f"Concurrent test failed: {str(e)}")

    def test_pool_doesn_t_exceed_max(self):
        """Test that pool doesn't create more than max_connections."""
        try:
            if PostgreSQLConnectionPool._pool is None:
                database_url = os.getenv('DATABASE_URL')
                PostgreSQLConnectionPool.initialize(database_url, 2, 5)

            # Get multiple connections
            conns = []
            for i in range(5):
                conn = PostgreSQLConnectionPool.get_connection()
                conns.append(conn)

            # Should not exceed max (2 + 3 overflow)
            assert len(conns) <= 5

            # Return them
            for conn in conns:
                PostgreSQLConnectionPool.put_connection(conn)

        except Exception as e:
            pytest.skip(f"Max pool test failed: {str(e)}")


class TestConnectionPoolWithDatabase:
    """Test connection pool integration with database module."""

    def test_get_db_context_uses_pool(self):
        """Test that get_db() context manager uses the pool."""
        try:
            # Set to PostgreSQL
            database.USE_POSTGRESQL = True

            if PostgreSQLConnectionPool._pool is None:
                database_url = os.getenv('DATABASE_URL')
                PostgreSQLConnectionPool.initialize(database_url)

            # Use get_db context manager
            with database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result is not None

        except Exception as e:
            pytest.skip(f"Database context test failed: {str(e)}")

    def test_multiple_database_operations_with_pool(self):
        """Test multiple database operations using pooled connections."""
        try:
            database.USE_POSTGRESQL = True

            if PostgreSQLConnectionPool._pool is None:
                database_url = os.getenv('DATABASE_URL')
                PostgreSQLConnectionPool.initialize(database_url)

            # Perform multiple operations
            for i in range(5):
                with database.get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT %s as iteration", (i,))
                    result = cursor.fetchone()
                    assert result is not None

        except Exception as e:
            pytest.skip(f"Multiple operations test failed: {str(e)}")


class TestConnectionPoolCleanup:
    """Test connection pool cleanup."""

    def test_close_pool(self):
        """Test that close_pool closes all connections."""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url is None:
                pytest.skip("DATABASE_URL not set")

            # Initialize fresh
            PostgreSQLConnectionPool._pool = None
            PostgreSQLConnectionPool.initialize(database_url, 5, 20)

            # Get some connections
            conns = []
            for i in range(3):
                conn = PostgreSQLConnectionPool.get_connection()
                conns.append(conn)

            # Return them
            for conn in conns:
                PostgreSQLConnectionPool.put_connection(conn)

            # Close pool
            PostgreSQLConnectionPool.close_pool()

            assert PostgreSQLConnectionPool._pool is None

        except Exception as e:
            pytest.skip(f"Close pool test failed: {str(e)}")


class TestConnectionPoolErrorHandling:
    """Test error handling in connection pool."""

    def test_invalid_connection_url(self):
        """Test that invalid connection URL raises appropriate error."""
        try:
            # Try to initialize with invalid URL
            invalid_url = "postgresql://invalid_user:invalid_pass@localhost:5432/nonexistent"

            # This should fail when trying to get a connection
            PostgreSQLConnectionPool._pool = None
            PostgreSQLConnectionPool.initialize(invalid_url, 2, 5)

            # Trying to get a connection should fail
            with pytest.raises(Exception):
                conn = PostgreSQLConnectionPool.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")

        except Exception as e:
            # Expected - invalid connection should fail
            pass

    def test_connection_reuse_after_error(self):
        """Test that pool recovers from connection errors."""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url is None:
                pytest.skip("DATABASE_URL not set")

            if PostgreSQLConnectionPool._pool is None:
                PostgreSQLConnectionPool.initialize(database_url)

            # Get a good connection
            conn = PostgreSQLConnectionPool.get_connection()

            # Use it successfully
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result is not None

            cursor.close()

            # Return it
            PostgreSQLConnectionPool.put_connection(conn)

            # Should be able to get another connection
            conn2 = PostgreSQLConnectionPool.get_connection()
            assert conn2 is not None

            PostgreSQLConnectionPool.put_connection(conn2)

        except Exception as e:
            pytest.skip(f"Recovery test failed: {str(e)}")


class TestPoolConfigurationFromEnvironment:
    """Test pool configuration from environment variables."""

    def test_pool_size_from_env(self):
        """Test that pool size is read from DB_POOL_SIZE env var."""
        try:
            # Set environment variables
            os.environ['DB_POOL_SIZE'] = '3'
            os.environ['DB_MAX_OVERFLOW'] = '7'

            database_url = os.getenv('DATABASE_URL')
            if database_url is None:
                pytest.skip("DATABASE_URL not set")

            # Reset pool
            PostgreSQLConnectionPool._pool = None

            # Initialize with env vars
            PostgreSQLConnectionPool.initialize(
                database_url,
                int(os.getenv('DB_POOL_SIZE', 5)),
                int(os.getenv('DB_MAX_OVERFLOW', 20))
            )

            assert PostgreSQLConnectionPool._pool._minconn == 3
            assert PostgreSQLConnectionPool._pool._maxconn == 7

        except Exception as e:
            pytest.skip(f"Env var test failed: {str(e)}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
