"""User Repository - User Account Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from orm.models.user import User
from repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user accounts."""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.session.query(User).filter(
            User.username == username
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.session.query(User).filter(
            User.email == email
        ).first()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users."""
        return self.session.query(User).filter(
            User.is_active == 1
        ).offset(skip).limit(limit).all()

    def get_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role."""
        return self.session.query(User).filter(
            User.role == role
        ).offset(skip).limit(limit).all()

    def authenticate(self, username: str, password_hash: str) -> Optional[User]:
        """Authenticate user (caller must verify hash)."""
        user = self.get_by_username(username)
        if user and user.is_active == 1:
            return user
        return None

    def update_last_login(self, user_id: str, ip_address: str) -> Optional[User]:
        """Update last login timestamp."""
        from datetime import datetime, timezone
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.now(timezone.utc).isoformat()
            user.last_login_ip = ip_address
            user.failed_login_attempts = 0
            self.session.flush()
        return user

    def increment_failed_attempts(self, user_id: str) -> Optional[User]:
        """Increment failed login attempts."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.is_active = 0  # Lock account after 5 attempts
            self.session.flush()
        return user

    def reset_failed_attempts(self, user_id: str) -> Optional[User]:
        """Reset failed login attempts."""
        user = self.get_by_id(user_id)
        if user:
            user.failed_login_attempts = 0
            self.session.flush()
        return user

    def deactivate(self, user_id: str) -> Optional[User]:
        """Deactivate user account."""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = 0
            self.session.flush()
        return user

    def activate(self, user_id: str) -> Optional[User]:
        """Activate user account."""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = 1
            user.failed_login_attempts = 0
            self.session.flush()
        return user

    def count_by_role(self, role: str) -> int:
        """Count users by role."""
        return self.session.query(User).filter(
            User.role == role
        ).count()
