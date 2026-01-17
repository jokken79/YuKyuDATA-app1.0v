"""
Database operations - Backup and restore operations
Part of the modularized YuKyuDATA database layer
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

from database import get_db, USE_POSTGRESQL, _convert_query_placeholders
from services.crypto_utils import encrypt_field, decrypt_field, get_encryption_manager

def get_db_path():
    """Get database path, handling Vercel serverless environment."""
    custom_path = os.getenv('DATABASE_PATH')
    if custom_path:
        return custom_path

    # Check if running on Vercel (serverless)
    if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        # Use /tmp for serverless (ephemeral storage)
        return '/tmp/yukyu.db'

    # Default: local directory
    return 'yukyu.db'

DB_NAME = get_db_path()
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DB_NAME}')

# Initialize connection manager for PostgreSQL
if USE_POSTGRESQL:
    db_manager = ConnectionManager(DATABASE_URL)
else:
    db_manager = None

def _get_param_placeholder() -> str:
    """Get parameter placeholder for current database."""
    return '%s' if USE_POSTGRESQL else '?'

def _convert_query_placeholders(query: str) -> str:
    """Convert SQLite ? placeholders to PostgreSQL %s if needed."""
    if not USE_POSTGRESQL:
        return query
    # Simple conversion - be careful with strings containing ?
    return query.replace('?', '%s')

def get_db_connection():
    """Get database connection (SQLite or PostgreSQL)."""
    if USE_POSTGRESQL:
        return db_manager.get_connection()
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


@contextmanager
def get_db() -> Generator:
    """Context manager for database connections to prevent memory leaks."""
    if USE_POSTGRESQL:
        # PostgreSQL connection from pool
        with db_manager.get_connection() as conn:
            yield conn
    else:
        # SQLite direct connection
        import sqlite3
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def init_db():
"""
Backup and restore operations for database.
Handles creating, listing, and restoring database backups.
"""

# ============================================

def create_backup(backup_dir="backups"):
    """
    Crea una copia de seguridad de la base de datos.

    Args:
        backup_dir: Directorio donde guardar backups

    Returns:
        dict con info del backup
    """
    import shutil

    # Create backup directory if not exists
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"yukyu_backup_{timestamp}.db"
    backup_filepath = backup_path / backup_filename

    # Copy database file
    if not Path(DB_NAME).exists():
        raise ValueError(f"Database file {DB_NAME} not found")

    shutil.copy2(DB_NAME, backup_filepath)

    # Get backup file size
    file_size = backup_filepath.stat().st_size

    # Clean old backups (keep last 10)
    backups = sorted(backup_path.glob("yukyu_backup_*.db"), reverse=True)
    for old_backup in backups[10:]:
        old_backup.unlink()

    return {
        "filename": backup_filename,
        "path": str(backup_filepath),
        "size_bytes": file_size,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "created_at": timestamp
    }


def list_backups(backup_dir="backups"):
    """
    Lista todos los backups disponibles.

    Returns:
        Lista de backups con info
    """
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        return []

    backups = []
    for backup_file in sorted(backup_path.glob("yukyu_backup_*.db"), reverse=True):
        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "path": str(backup_file),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return backups


def restore_backup(backup_filename, backup_dir="backups"):
    """
    Restaura la base de datos desde un backup.
    CUIDADO: Esto sobrescribe la base de datos actual.

    Args:
        backup_filename: Nombre del archivo de backup
        backup_dir: Directorio de backups

    Returns:
        dict con info de la restauración
    """
    import shutil

    backup_path = Path(backup_dir) / backup_filename

    if not backup_path.exists():
        raise ValueError(f"Backup file {backup_filename} not found")

    # Create a backup of current DB before restoring
    current_backup = create_backup(backup_dir)

    # Restore the backup
    shutil.copy2(backup_path, DB_NAME)

    return {
        "restored_from": backup_filename,
        "previous_backup": current_backup['filename'],
        "restored_at": datetime.now().isoformat()
    }


# ============================================
# AUDIT LOG FUNCTIONS (v2.3 - Complete Audit Trail)
