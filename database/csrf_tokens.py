"""
CSRF Token Management Module
Provides stateful CSRF token validation with persistent storage
"""

import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy import Column, String, DateTime, Integer, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# Base declarative for CSRF token model
Base = declarative_base()


class CSRFToken(Base):
    """CSRF token model for database persistence"""
    __tablename__ = "csrf_tokens"

    id = Column(String(36), primary_key=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    session_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Integer, default=0, nullable=False)  # 0=not used, 1=used
    used_at = Column(DateTime, nullable=True)


def init_csrf_tokens_table(session: Session) -> bool:
    """
    Initialize CSRF tokens table in database.
    Safe to call multiple times (idempotent).

    Args:
        session: SQLAlchemy session

    Returns:
        bool: True if table was created or already exists
    """
    try:
        # Check if table exists
        from sqlalchemy import inspect
        inspector = inspect(session.bind)

        if "csrf_tokens" not in inspector.get_table_names():
            Base.metadata.create_all(session.bind)
            logger.info("Created csrf_tokens table")

        return True
    except Exception as e:
        logger.error(f"Error initializing CSRF tokens table: {e}")
        return False


def _hash_token(token: str) -> str:
    """
    Generate SHA-256 hash of CSRF token for storage.
    Never store plain tokens, only hashes.

    Args:
        token: Plain CSRF token

    Returns:
        str: SHA-256 hash in hexadecimal
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def store_csrf_token(
    session: Session,
    token: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    expires_in_minutes: int = 30
) -> Tuple[bool, Optional[str]]:
    """
    Store CSRF token in database with expiration.

    Args:
        session: SQLAlchemy session
        token: Plain CSRF token (will be hashed)
        user_id: Optional user ID for auditing
        session_id: Optional session ID for tracking
        expires_in_minutes: Token expiration time in minutes (default 30)

    Returns:
        Tuple[bool, Optional[str]]: (success, error_message)
    """
    try:
        import uuid

        token_hash = _hash_token(token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        csrf_record = CSRFToken(
            id=str(uuid.uuid4()),
            token_hash=token_hash,
            user_id=user_id,
            session_id=session_id,
            expires_at=expires_at
        )

        session.add(csrf_record)
        session.commit()

        logger.debug(f"CSRF token stored (expires in {expires_in_minutes}min)")
        return True, None

    except Exception as e:
        session.rollback()
        logger.error(f"Error storing CSRF token: {e}")
        return False, str(e)


def validate_csrf_token(
    session: Session,
    token: str,
    mark_used: bool = True
) -> Tuple[bool, str]:
    """
    Validate CSRF token against stored tokens in database.
    Implements stateful CSRF protection (not stateless).

    Args:
        session: SQLAlchemy session
        token: Token to validate
        mark_used: If True, mark token as used (single-use enforcement)

    Returns:
        Tuple[bool, str]: (is_valid, reason)
        - (True, "Valid") if token is valid
        - (False, reason) if token is invalid/expired/already used
    """
    try:
        if not token or len(token) < 20:
            return False, "Token format invalid"

        token_hash = _hash_token(token)
        now = datetime.now(timezone.utc)

        # Query for token in database
        csrf_record = session.query(CSRFToken).filter(
            CSRFToken.token_hash == token_hash
        ).first()

        if not csrf_record:
            logger.warning(f"CSRF token not found in database")
            return False, "Token not found"

        # Check expiration
        if csrf_record.expires_at < now:
            logger.warning(f"CSRF token expired")
            return False, "Token expired"

        # Check single-use constraint
        if csrf_record.is_used:
            logger.warning(f"CSRF token already used")
            return False, "Token already used"

        # Mark as used if requested
        if mark_used:
            csrf_record.is_used = 1
            csrf_record.used_at = now
            session.commit()
            logger.debug(f"CSRF token marked as used")

        return True, "Valid"

    except Exception as e:
        logger.error(f"Error validating CSRF token: {e}")
        return False, f"Validation error: {str(e)}"


def cleanup_expired_csrf_tokens(session: Session, hours: int = 24) -> int:
    """
    Delete expired CSRF tokens older than specified hours.
    Should be called periodically (e.g., via cron job).

    Args:
        session: SQLAlchemy session
        hours: Delete tokens older than this many hours (default 24)

    Returns:
        int: Number of tokens deleted
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)

        deleted_count = session.query(CSRFToken).filter(
            CSRFToken.expires_at < cutoff_date
        ).delete()

        session.commit()

        logger.info(f"Cleaned up {deleted_count} expired CSRF tokens")
        return deleted_count

    except Exception as e:
        session.rollback()
        logger.error(f"Error cleaning up CSRF tokens: {e}")
        return 0


def get_csrf_token_stats(session: Session) -> dict:
    """
    Get statistics about CSRF tokens in database.
    Useful for monitoring and debugging.

    Args:
        session: SQLAlchemy session

    Returns:
        dict: Stats with keys:
            - total: Total tokens
            - active: Not expired and not used
            - used: Marked as used
            - expired: Expired tokens
    """
    try:
        now = datetime.now(timezone.utc)

        total = session.query(CSRFToken).count()
        active = session.query(CSRFToken).filter(
            CSRFToken.expires_at > now,
            CSRFToken.is_used == 0
        ).count()
        used = session.query(CSRFToken).filter(
            CSRFToken.is_used == 1
        ).count()
        expired = session.query(CSRFToken).filter(
            CSRFToken.expires_at <= now
        ).count()

        return {
            "total": total,
            "active": active,
            "used": used,
            "expired": expired
        }

    except Exception as e:
        logger.error(f"Error getting CSRF token stats: {e}")
        return {"error": str(e)}
