"""
Refresh Token Management Module
Provides persistent storage for JWT refresh tokens with session tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from orm import SessionLocal, Base, engine

logger = logging.getLogger(__name__)

# Import model lazily to avoid circular imports
_RefreshToken = None


def _get_model():
    """Lazy import of RefreshToken model."""
    global _RefreshToken
    if _RefreshToken is None:
        from orm.models.refresh_token import RefreshToken
        _RefreshToken = RefreshToken
    return _RefreshToken


def init_refresh_tokens_table() -> bool:
    """
    Initialize refresh_tokens table in database.
    Safe to call multiple times (idempotent).

    Returns:
        bool: True if table was created or already exists
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)

        if "refresh_tokens" not in inspector.get_table_names():
            RefreshToken = _get_model()
            Base.metadata.create_all(engine, tables=[RefreshToken.__table__])
            logger.info("Created refresh_tokens table")

        return True
    except Exception as e:
        logger.error(f"Error initializing refresh_tokens table: {e}")
        return False


def store_refresh_token(
    token_id: str,
    user_id: str,
    token_hash: str,
    expires_at: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None
) -> bool:
    """
    Store a refresh token in the database.

    Args:
        token_id: Unique JWT ID (jti claim) - stored as primary key 'id'
        user_id: Username who owns the token
        token_hash: SHA-256 hash of the token
        expires_at: ISO format expiration datetime
        user_agent: Client User-Agent string
        ip_address: Client IP address

    Returns:
        bool: True if stored successfully
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            record = RefreshToken(
                id=token_id,
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at if isinstance(expires_at, str) else expires_at.isoformat(),
                created_at=datetime.now(timezone.utc).isoformat(),
                user_agent=user_agent,
                ip_address=ip_address
            )
            session.add(record)
            session.commit()
            logger.debug(f"Refresh token stored for user {user_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing refresh token: {e}")
            return False


def get_refresh_token_by_hash(token_hash: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a refresh token record by its hash.

    Args:
        token_hash: SHA-256 hash of the token

    Returns:
        Dict with token data or None if not found
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            record = session.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash
            ).first()

            if record:
                return {
                    "id": record.id,
                    "user_id": record.user_id,
                    "token_hash": record.token_hash,
                    "expires_at": record.expires_at,
                    "created_at": record.created_at,
                    "revoked": record.revoked,
                    "revoked_at": record.revoked_at,
                    "user_agent": record.user_agent,
                    "ip_address": record.ip_address,
                }
            return None
        except Exception as e:
            logger.error(f"Error getting refresh token: {e}")
            return None


def is_refresh_token_valid(token_hash: str) -> bool:
    """
    Check if a refresh token is valid (exists, not revoked, not expired).

    Args:
        token_hash: SHA-256 hash of the token

    Returns:
        bool: True if token is valid
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            now = datetime.now(timezone.utc).isoformat()
            record = session.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == 0,
                RefreshToken.expires_at > now
            ).first()

            return record is not None
        except Exception as e:
            logger.error(f"Error checking refresh token validity: {e}")
            return False


def revoke_refresh_token(token_hash: str) -> bool:
    """
    Revoke a refresh token by its hash.

    Args:
        token_hash: SHA-256 hash of the token to revoke

    Returns:
        bool: True if revoked successfully
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            record = session.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == 0
            ).first()

            if record:
                record.revoked = 1
                record.revoked_at = datetime.now(timezone.utc).isoformat()
                session.commit()
                logger.debug("Refresh token revoked")
                return True

            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error revoking refresh token: {e}")
            return False


def revoke_all_user_refresh_tokens(user_id: str) -> int:
    """
    Revoke all active refresh tokens for a user (logout all sessions).

    Args:
        user_id: Username whose tokens to revoke

    Returns:
        int: Number of tokens revoked
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            now = datetime.now(timezone.utc).isoformat()
            tokens = session.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == 0
            ).all()

            count = 0
            for token in tokens:
                token.revoked = 1
                token.revoked_at = now
                count += 1

            session.commit()
            logger.info(f"Revoked {count} refresh tokens for user {user_id}")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error revoking all user tokens: {e}")
            return 0


def get_user_active_refresh_tokens(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all active (non-revoked, non-expired) refresh tokens for a user.

    Args:
        user_id: Username to query

    Returns:
        List of token records (without the hash for security)
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            now = datetime.now(timezone.utc).isoformat()
            tokens = session.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == 0,
                RefreshToken.expires_at > now
            ).order_by(RefreshToken.created_at.desc()).all()

            return [
                {
                    "token_id": t.id,
                    "user_id": t.user_id,
                    "created_at": t.created_at,
                    "expires_at": t.expires_at,
                    "user_agent": t.user_agent,
                    "ip_address": t.ip_address,
                }
                for t in tokens
            ]
        except Exception as e:
            logger.error(f"Error getting user active tokens: {e}")
            return []


def cleanup_expired_refresh_tokens(hours: int = 24) -> int:
    """
    Delete expired or revoked refresh tokens older than specified hours.

    Args:
        hours: Delete tokens expired/revoked more than this many hours ago

    Returns:
        int: Number of tokens deleted
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            from datetime import timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

            deleted = session.query(RefreshToken).filter(
                (RefreshToken.expires_at < cutoff) |
                ((RefreshToken.revoked == 1) & (RefreshToken.revoked_at < cutoff))
            ).delete(synchronize_session='fetch')

            session.commit()
            logger.info(f"Cleaned up {deleted} expired/revoked refresh tokens")
            return deleted
        except Exception as e:
            session.rollback()
            logger.error(f"Error cleaning up refresh tokens: {e}")
            return 0


def get_refresh_token_stats() -> Dict[str, Any]:
    """
    Get statistics about refresh tokens in database.

    Returns:
        dict with keys: total, active, revoked, expired
    """
    RefreshToken = _get_model()

    with SessionLocal() as session:
        try:
            now = datetime.now(timezone.utc).isoformat()

            total = session.query(RefreshToken).count()
            active = session.query(RefreshToken).filter(
                RefreshToken.revoked == 0,
                RefreshToken.expires_at > now
            ).count()
            revoked = session.query(RefreshToken).filter(
                RefreshToken.revoked == 1
            ).count()
            expired = session.query(RefreshToken).filter(
                RefreshToken.expires_at <= now,
                RefreshToken.revoked == 0
            ).count()

            return {
                "total": total,
                "active": active,
                "revoked": revoked,
                "expired": expired
            }
        except Exception as e:
            logger.error(f"Error getting refresh token stats: {e}")
            return {"error": str(e)}
