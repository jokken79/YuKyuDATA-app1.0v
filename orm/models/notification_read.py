"""NotificationRead ORM Model - Notification Read Status"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from orm.models.base import Base, BaseModel


class NotificationRead(BaseModel, Base):
    """
    Tracks which notifications have been read by which users.

    Enables multi-user notification tracking where same notification
    can be marked as read by different users independently.

    Attributes:
        id: UUID primary key
        user_id: User who read the notification (indexed)
        notification_id: Notification that was read (indexed)
        read_at: Timestamp when notification was marked as read
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was updated
    """

    __tablename__ = "notification_reads"

    user_id = Column(String(50), nullable=False, index=True)
    notification_id = Column(String(36), nullable=False, index=True)
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint to prevent duplicate reads
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_id', name='uq_user_notif'),
        Index('idx_notif_read_user', 'user_id'),
        Index('idx_notif_read_notif', 'notification_id'),
        Index('idx_notif_read_at', 'read_at'),
    )

    def __repr__(self):
        return f"<NotificationRead(user_id={self.user_id}, notification_id={self.notification_id})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_id': self.notification_id,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
