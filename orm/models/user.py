"""User ORM Model - System Users"""

from sqlalchemy import Column, String, Integer, Index
from orm.models.base import Base, BaseModel


class User(BaseModel, Base):
    """
    System user account.

    Attributes:
        id: UUID primary key
        username: Unique username (indexed)
        email: User email (indexed)
        password_hash: Bcrypt hashed password (never store plain text)
        full_name: User's full name
        role: User role (admin, manager, employee)
        is_active: Whether account is active
        last_login: Timestamp of last login
        last_login_ip: IP address of last login
        failed_login_attempts: Counter for security
        created_at: Account creation timestamp
        updated_at: Last account update timestamp
    """

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="employee")  # admin, manager, employee
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive
    last_login = Column(String(19))  # ISO format datetime
    last_login_ip = Column(String(45))  # Support IPv4 and IPv6
    failed_login_attempts = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    def to_dict(self, include_password=False):
        """Convert to dict for API responses."""
        result = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': bool(self.is_active),
            'last_login': self.last_login,
            'last_login_ip': self.last_login_ip,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_password:
            result['password_hash'] = self.password_hash

        return result
