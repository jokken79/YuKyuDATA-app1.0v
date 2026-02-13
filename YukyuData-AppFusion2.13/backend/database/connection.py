import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv

load_dotenv()

# Import database connection manager if available
try:
    from database.postgresql_provider import ConnectionManager
    USE_POSTGRESQL = os.getenv('DATABASE_TYPE', 'sqlite').lower() == 'postgresql'
except ImportError:
    USE_POSTGRESQL = False


def get_db_path():
    """Get database path, handling Vercel serverless environment."""
    custom_path = os.getenv('DATABASE_PATH')
    if custom_path:
        return custom_path

    # Check if running on Vercel (serverless)
    if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        # Force PostgreSQL on Vercel/Production if possible,
        # but keep SQLite as fallback to /tmp
        return '/tmp/yukyu.db'

    return 'yukyu.db'


DB_NAME = get_db_path()
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DB_NAME}')

if USE_POSTGRESQL:
    # This assumes db_manager will be initialized elsewhere or we handle it here
    db_manager = ConnectionManager(DATABASE_URL)
else:
    db_manager = None


@contextmanager
def get_db() -> Generator:
    """Context manager for database connections to prevent memory leaks."""
    if USE_POSTGRESQL and db_manager:
        with db_manager.get_connection() as conn:
            yield conn
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


def _get_param_placeholder() -> str:
    return '%s' if USE_POSTGRESQL else '?'


def _convert_query_placeholders(query: str) -> str:
    if not USE_POSTGRESQL:
        return query
    return query.replace('?', '%s')
