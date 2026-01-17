import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator, Dict, List, Any
from services.crypto_utils import encrypt_field, decrypt_field, get_encryption_manager

# Import database connection manager
try:
    from database.connection import ConnectionManager
    USE_POSTGRESQL = os.getenv('DATABASE_TYPE', 'sqlite').lower() == 'postgresql'
except ImportError:
    # Fallback for SQLite if connection manager not available
    import sqlite3
    USE_POSTGRESQL = False

# Vercel compatibility: Use /tmp for serverless or custom path via env var
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
Notification read status tracking.
Manages which users have read which notifications.
"""

# ============================================

def mark_notification_read(notification_id: str, user_id: str) -> bool:
    """
    Marca una notificación como leída para un usuario específico.

    Args:
        notification_id: ID de la notificación
        user_id: ID del usuario

    Returns:
        True si se marcó correctamente, False si ya estaba marcada
    """
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO notification_reads (notification_id, user_id, read_at)
                VALUES (?, ?, ?)
            ''', (notification_id, user_id, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Ya estaba marcada como leída (UNIQUE constraint)
            return False


def mark_all_notifications_read(user_id: str, notification_ids: list) -> int:
    """
    Marca múltiples notificaciones como leídas para un usuario.

    Args:
        user_id: ID del usuario
        notification_ids: Lista de IDs de notificaciones

    Returns:
        Número de notificaciones marcadas como leídas
    """
    if not notification_ids:
        return 0

    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        marked_count = 0

        for notif_id in notification_ids:
            try:
                c.execute('''
                    INSERT INTO notification_reads (notification_id, user_id, read_at)
                    VALUES (?, ?, ?)
                ''', (notif_id, user_id, timestamp))
                marked_count += 1
            except sqlite3.IntegrityError:
                # Ya estaba marcada
                pass

        conn.commit()
        return marked_count


def is_notification_read(notification_id: str, user_id: str) -> bool:
    """
    Verifica si una notificación ha sido leída por un usuario.

    Args:
        notification_id: ID de la notificación
        user_id: ID del usuario

    Returns:
        True si está leída, False si no
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 1 FROM notification_reads
            WHERE notification_id = ? AND user_id = ?
        ''', (notification_id, user_id))
        return c.fetchone() is not None


def get_read_notification_ids(user_id: str) -> set:
    """
    Obtiene todos los IDs de notificaciones leídas por un usuario.

    Args:
        user_id: ID del usuario

    Returns:
        Set de notification_ids que han sido leídas
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT notification_id FROM notification_reads
            WHERE user_id = ?
        ''', (user_id,))
        return {row['notification_id'] for row in c.fetchall()}


def get_unread_count(user_id: str, notification_ids: list) -> int:
    """
    Cuenta cuántas notificaciones no han sido leídas por un usuario.

    Args:
        user_id: ID del usuario
        notification_ids: Lista de IDs de notificaciones a verificar

    Returns:
        Número de notificaciones no leídas
    """
    if not notification_ids:
        return 0

    read_ids = get_read_notification_ids(user_id)
    return len([nid for nid in notification_ids if nid not in read_ids])


# ============================================
# REFRESH TOKENS TABLE & FUNCTIONS (v5.17)
# Secure token storage with database persistence
# ============================================

def init_refresh_tokens_table():
    """
    Crea la tabla refresh_tokens para almacenamiento seguro de tokens.
    Los refresh tokens se almacenan hasheados para mayor seguridad.
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                revoked INTEGER DEFAULT 0,
                revoked_at TEXT,
                user_agent TEXT,
                ip_address TEXT
            )
        ''')

        # Indices para búsquedas eficientes
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked ON refresh_tokens(revoked)')

        conn.commit()


def store_refresh_token(
    token_id: str,
    user_id: str,
    token_hash: str,
    expires_at: str,
    user_agent: str = None,
    ip_address: str = None
) -> bool:
    """
    Almacena un nuevo refresh token en la base de datos.

    Args:
        token_id: ID único del token (UUID)
        user_id: ID del usuario al que pertenece el token
        token_hash: Hash SHA-256 del token (nunca almacenar el token plano)
        expires_at: Fecha de expiración en formato ISO
        user_agent: User-Agent del cliente (opcional)
        ip_address: IP del cliente (opcional)

    Returns:
        True si se almacenó correctamente
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        try:
            if USE_POSTGRESQL:
                c.execute('''
                    INSERT INTO refresh_tokens
                    (id, user_id, token_hash, expires_at, created_at, user_agent, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (token_id, user_id, token_hash, expires_at, timestamp, user_agent, ip_address))
            else:
                c.execute('''
                    INSERT INTO refresh_tokens
                    (id, user_id, token_hash, expires_at, created_at, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (token_id, user_id, token_hash, expires_at, timestamp, user_agent, ip_address))

            conn.commit()
            return True
        except Exception as e:
            print(f"Error storing refresh token: {e}")
            return False


def get_refresh_token_by_hash(token_hash: str) -> Optional[Dict]:
    """
    Busca un refresh token por su hash.

    Args:
        token_hash: Hash SHA-256 del token

    Returns:
        Dict con los datos del token o None si no existe
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            SELECT * FROM refresh_tokens
            WHERE token_hash = ? AND revoked = 0
        ''', (token_hash,))

        row = c.fetchone()
        if row:
            return dict(row)
        return None


def get_refresh_token_by_id(token_id: str) -> Optional[Dict]:
    """
    Busca un refresh token por su ID.

    Args:
        token_id: ID del token

    Returns:
        Dict con los datos del token o None si no existe
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('SELECT * FROM refresh_tokens WHERE id = ?', (token_id,))

        row = c.fetchone()
        if row:
            return dict(row)
        return None


def revoke_refresh_token(token_hash: str) -> bool:
    """
    Revoca un refresh token específico.

    Args:
        token_hash: Hash del token a revocar

    Returns:
        True si se revocó correctamente
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        c.execute('''
            UPDATE refresh_tokens
            SET revoked = 1, revoked_at = ?
            WHERE token_hash = ? AND revoked = 0
        ''', (timestamp, token_hash))

        conn.commit()
        return c.rowcount > 0


def revoke_refresh_token_by_id(token_id: str) -> bool:
    """
    Revoca un refresh token por su ID.

    Args:
        token_id: ID del token a revocar

    Returns:
        True si se revocó correctamente
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        c.execute('''
            UPDATE refresh_tokens
            SET revoked = 1, revoked_at = ?
            WHERE id = ? AND revoked = 0
        ''', (timestamp, token_id))

        conn.commit()
        return c.rowcount > 0


def revoke_all_user_refresh_tokens(user_id: str) -> int:
    """
    Revoca todos los refresh tokens de un usuario (logout de todas las sesiones).

    Args:
        user_id: ID del usuario

    Returns:
        Número de tokens revocados
    """
    with get_db() as conn:
        c = conn.cursor()
        timestamp = datetime.now().isoformat()

        c.execute('''
            UPDATE refresh_tokens
            SET revoked = 1, revoked_at = ?
            WHERE user_id = ? AND revoked = 0
        ''', (timestamp, user_id))

        revoked_count = c.rowcount
        conn.commit()
        return revoked_count


def get_user_active_refresh_tokens(user_id: str) -> List[Dict]:
    """
    Obtiene todos los refresh tokens activos de un usuario.

    Args:
        user_id: ID del usuario

    Returns:
        Lista de tokens activos (sin el hash por seguridad)
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute('''
            SELECT id, user_id, expires_at, created_at, user_agent, ip_address
            FROM refresh_tokens
            WHERE user_id = ? AND revoked = 0 AND expires_at > ?
            ORDER BY created_at DESC
        ''', (user_id, datetime.now().isoformat()))

        rows = c.fetchall()
        return [dict(row) for row in rows]


def cleanup_expired_refresh_tokens() -> int:
    """
    Elimina todos los refresh tokens expirados o revocados.
    Debe ejecutarse periódicamente (ej: cada hora o diariamente).

    Returns:
        Número de tokens eliminados
    """
    with get_db() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()

        # Eliminar tokens expirados (más de 7 días después de expiración)
        # o tokens revocados hace más de 24 horas
        cutoff_date = (datetime.now() - timedelta(days=1)).isoformat()

        c.execute('''
            DELETE FROM refresh_tokens
            WHERE expires_at < ? OR (revoked = 1 AND revoked_at < ?)
        ''', (now, cutoff_date))

        deleted_count = c.rowcount
        conn.commit()
        return deleted_count


def is_refresh_token_valid(token_hash: str) -> bool:
    """
    Verifica si un refresh token es válido (existe, no revocado, no expirado).

    Args:
        token_hash: Hash del token

    Returns:
        True si el token es válido
    """
    with get_db() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()

        c.execute('''
            SELECT 1 FROM refresh_tokens
            WHERE token_hash = ? AND revoked = 0 AND expires_at > ?
        ''', (token_hash, now))

        return c.fetchone() is not None


def get_refresh_token_stats() -> Dict:
    """
    Obtiene estadísticas de los refresh tokens.

    Returns:
        Dict con estadísticas (total, activos, revocados, expirados)
    """
    with get_db() as conn:
        c = conn.cursor()
        now = datetime.now().isoformat()

        # Total de tokens
        c.execute('SELECT COUNT(*) as count FROM refresh_tokens')
        total = c.fetchone()['count']

        # Tokens activos
        c.execute('''
            SELECT COUNT(*) as count FROM refresh_tokens
            WHERE revoked = 0 AND expires_at > ?
        ''', (now,))
        active = c.fetchone()['count']

        # Tokens revocados
        c.execute('SELECT COUNT(*) as count FROM refresh_tokens WHERE revoked = 1')
        revoked = c.fetchone()['count']

        # Tokens expirados (no revocados pero expirados)
        c.execute('''
            SELECT COUNT(*) as count FROM refresh_tokens
            WHERE revoked = 0 AND expires_at <= ?
        ''', (now,))
        expired = c.fetchone()['count']

        # Usuarios únicos con tokens activos
        c.execute('''
            SELECT COUNT(DISTINCT user_id) as count FROM refresh_tokens
            WHERE revoked = 0 AND expires_at > ?
        ''', (now,))
        unique_users = c.fetchone()['count']

        return {
            "total": total,
            "active": active,
            "revoked": revoked,
            "expired": expired,
            "unique_users_with_sessions": unique_users
        }
