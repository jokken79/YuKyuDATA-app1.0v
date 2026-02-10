"""Refresh Token ORM Model for JWT refresh token persistence"""

from sqlalchemy import Column, String, DateTime, Integer, Index, Text
from orm import Base
from datetime import datetime, timezone


class RefreshToken(Base):
    """
    Refresh token model for database persistence.

    Stores hashed refresh tokens with metadata for session tracking,
    revocation, and cleanup of expired tokens.

    Note: Matches existing refresh_tokens table schema in yukyu.db.
    The 'id' column stores the JWT token_id (jti claim).
    """
    __tablename__ = "refresh_tokens"
    __table_args__ = {'extend_existing': True}

    id = Column(Text, primary_key=True)
    user_id = Column(Text, nullable=False, index=True)
    token_hash = Column(Text, unique=True, nullable=False, index=True)
    expires_at = Column(Text, nullable=False)
    created_at = Column(Text, default=lambda: datetime.now(timezone.utc).isoformat())
    revoked = Column(Integer, default=0, nullable=False)
    revoked_at = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(Text, nullable=True)
