"""
Database Connection Management
Handles both SQLite and PostgreSQL connections with pooling support.

For SQLite: Direct connection (no pooling)
For PostgreSQL: psycopg2 ThreadedConnectionPool for concurrent access
"""

import os
import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional, Generator

# PostgreSQL imports (optional for backward compatibility)
try:
    import psycopg2
    from psycopg2 import pool as psycopg2_pool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)


class SQLiteConnection:
    """Simple SQLite connection wrapper"""

    def __init__(self, db_path: str = "yukyu.db"):
        self.db_path = db_path
        self.connection = None

    def connect(self) -> sqlite3.Connection:
        """Create SQLite connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        logger.info(f"Connected to SQLite: {self.db_path}")
        return conn

    def close(self):
        """Close connection if open"""
        if self.connection:
            self.connection.close()
            logger.info("SQLite connection closed")


class PostgreSQLConnectionPool:
    """PostgreSQL connection pool manager using psycopg2.pool.ThreadedConnectionPool"""

    _pool: Optional[psycopg2_pool.ThreadedConnectionPool] = None
    _initialized = False

    @classmethod
    def initialize(cls, database_url: str, min_connections: int = 5, max_connections: int = 20):
        """
        Initialize PostgreSQL connection pool on application startup.

        Args:
            database_url: PostgreSQL connection string
                         Format: postgresql+psycopg2://user:password@host:port/dbname
            min_connections: Minimum connections to maintain
            max_connections: Maximum connections allowed

        Raises:
            RuntimeError: If psycopg2 is not available
        """
        if not PSYCOPG2_AVAILABLE:
            raise RuntimeError("psycopg2 not installed. Run: pip install -r requirements-db.txt")

        if cls._initialized:
            logger.warning("Connection pool already initialized, skipping re-initialization")
            return

        try:
            # Parse PostgreSQL URL to psycopg2 DSN format
            # Convert: postgresql+psycopg2://user:pass@host:port/dbname
            # To: dbname=X user=X password=X host=X port=X
            dsn = cls._parse_database_url(database_url)

            cls._pool = psycopg2_pool.ThreadedConnectionPool(
                minconn=min_connections,
                maxconn=max_connections,
                dsn=dsn
            )
            cls._initialized = True
            logger.info(
                f"PostgreSQL connection pool initialized: "
                f"min={min_connections}, max={max_connections}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            raise RuntimeError(f"Database pool initialization failed: {e}")

    @classmethod
    def get_connection(cls) -> psycopg2.extensions.connection:
        """
        Get a connection from the pool.

        Returns:
            psycopg2 connection object

        Raises:
            RuntimeError: If pool not initialized
        """
        if not cls._initialized or cls._pool is None:
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")

        try:
            conn = cls._pool.getconn()
            conn.set_client_encoding('UTF8')
            return conn
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise

    @classmethod
    def put_connection(cls, conn: psycopg2.extensions.connection) -> None:
        """
        Return a connection to the pool.

        Args:
            conn: Connection object to return
        """
        if cls._pool is None:
            if conn:
                conn.close()
            return

        try:
            cls._pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
            if conn:
                conn.close()

    @classmethod
    def close_all(cls) -> None:
        """Close all connections in the pool. Call on application shutdown."""
        if cls._pool is not None:
            try:
                cls._pool.closeall()
                cls._pool = None
                cls._initialized = False
                logger.info("PostgreSQL connection pool closed")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")

    @classmethod
    def get_pool_status(cls) -> dict:
        """
        Get current pool status.

        Returns:
            Dictionary with pool statistics
        """
        if cls._pool is None:
            return {"status": "not_initialized"}

        try:
            # psycopg2 pool doesn't expose connection count directly,
            # so we return basic status
            return {
                "status": "active",
                "pool_type": "ThreadedConnectionPool",
                "info": "Use monitoring queries to get detailed stats"
            }
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {"status": "error", "error": str(e)}

    @staticmethod
    def _parse_database_url(url: str) -> str:
        """
        Convert PostgreSQL connection URL to psycopg2 DSN format.

        Converts: postgresql+psycopg2://user:password@host:port/dbname
        To: dbname=X user=X password=X host=X port=X

        Args:
            url: PostgreSQL connection URL

        Returns:
            psycopg2 DSN string
        """
        try:
            from urllib.parse import urlparse

            # Handle both postgresql:// and postgresql+psycopg2:// schemes
            if url.startswith('postgresql+psycopg2://'):
                url = url.replace('postgresql+psycopg2://', 'postgresql://')
            elif not url.startswith('postgresql://'):
                raise ValueError(f"Invalid PostgreSQL URL scheme: {url}")

            parsed = urlparse(url)

            dsn_parts = []

            if parsed.hostname:
                dsn_parts.append(f"host={parsed.hostname}")
            if parsed.port:
                dsn_parts.append(f"port={parsed.port}")
            if parsed.username:
                dsn_parts.append(f"user={parsed.username}")
            if parsed.password:
                dsn_parts.append(f"password={parsed.password}")
            if parsed.path and len(parsed.path) > 1:
                dbname = parsed.path.lstrip('/')
                dsn_parts.append(f"dbname={dbname}")

            return ' '.join(dsn_parts)
        except Exception as e:
            logger.error(f"Error parsing database URL: {e}")
            raise ValueError(f"Failed to parse PostgreSQL URL: {e}")


class ConnectionManager:
    """
    Unified connection manager supporting both SQLite and PostgreSQL.
    Provides a consistent interface regardless of database type.
    """

    def __init__(self, database_url: str = None, pool_size: int = 10, max_overflow: int = 20):
        """
        Initialize connection manager.

        Args:
            database_url: Database connection URL (from env or config)
            pool_size: Minimum connections for PostgreSQL pool
            max_overflow: Maximum additional connections for PostgreSQL pool
        """
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///./yukyu.db')
        self.database_type = self._detect_database_type(self.database_url)
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.sqlite_conn: Optional[SQLiteConnection] = None

        logger.info(f"ConnectionManager initialized: type={self.database_type}")

        # Initialize appropriate backend
        if self.database_type == 'postgresql':
            if not PSYCOPG2_AVAILABLE:
                raise RuntimeError(
                    "PostgreSQL selected but psycopg2 not installed. "
                    "Run: pip install -r requirements-db.txt"
                )
            PostgreSQLConnectionPool.initialize(
                database_url=self.database_url,
                min_connections=pool_size,
                max_connections=pool_size + max_overflow
            )
        else:
            # SQLite
            db_path = self.database_url.replace('sqlite:///', '').replace('sqlite://', '')
            self.sqlite_conn = SQLiteConnection(db_path=db_path)

    @contextmanager
    def get_connection(self) -> Generator:
        """
        Get a database connection (context manager).

        Usage:
            with manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)

        Yields:
            Database connection object
        """
        if self.database_type == 'postgresql':
            conn = PostgreSQLConnectionPool.get_connection()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise
            finally:
                PostgreSQLConnectionPool.put_connection(conn)
        else:
            conn = self.sqlite_conn.connect()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise
            finally:
                conn.close()

    def close(self) -> None:
        """Close all connections. Call on application shutdown."""
        if self.database_type == 'postgresql':
            PostgreSQLConnectionPool.close_all()
        elif self.sqlite_conn:
            self.sqlite_conn.close()

        logger.info("ConnectionManager closed")

    def get_status(self) -> dict:
        """Get database connection status"""
        status = {
            "database_type": self.database_type,
            "database_url": self._mask_password(self.database_url),
        }

        if self.database_type == 'postgresql':
            status.update(PostgreSQLConnectionPool.get_pool_status())
        else:
            status['status'] = 'ready'

        return status

    @staticmethod
    def _detect_database_type(database_url: str) -> str:
        """Detect database type from URL"""
        if database_url.startswith('postgresql://') or database_url.startswith('postgresql+'):
            return 'postgresql'
        return 'sqlite'

    @staticmethod
    def _mask_password(url: str) -> str:
        """Mask password in URL for logging"""
        if ':' in url and '@' in url:
            scheme, rest = url.split('://', 1)
            user_part, host_part = rest.split('@', 1)
            user_only = user_part.split(':')[0]
            return f"{scheme}://{user_only}:***@{host_part}"
        return url


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def initialize_connections(database_url: str = None, pool_size: int = 10, max_overflow: int = 20) -> None:
    """
    Initialize global connection manager.
    Call this in FastAPI app.on_event("startup")
    """
    global _connection_manager
    _connection_manager = ConnectionManager(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow
    )


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager"""
    if _connection_manager is None:
        raise RuntimeError("Connection manager not initialized. Call initialize_connections() first.")
    return _connection_manager


def close_connections() -> None:
    """
    Close all database connections.
    Call this in FastAPI app.on_event("shutdown")
    """
    global _connection_manager
    if _connection_manager:
        _connection_manager.close()
        _connection_manager = None
