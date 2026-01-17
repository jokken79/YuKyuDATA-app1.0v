"""Notification ORM Model - System Notifications"""

from sqlalchemy import Column, String, Integer, Index
from sqlalchemy.orm import declarative_base
from orm.models.base import BaseModel

Base = declarative_base()


class Notification(BaseModel, Base):
    """
    System notification for users.

    Attributes:
        id: UUID primary key
        user_id: Target user ID (indexed)
        notification_type: Type of notification (leave_request, approval, expiring, etc)
        title: Notification title
        message: Notification message
        related_id: ID of related entity (e.g., leave_request_id)
        related_type: Type of related entity (leave_request, employee, etc)
        priority: Priority level (low, normal, high, critical)
        is_read: Whether notification has been read (deprecated, use NotificationRead)
        created_at: When notification was created
        updated_at: When notification was updated
    """

    __tablename__ = "notifications"

    user_id = Column(String(50), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(1000))
    related_id = Column(String(50))
    related_type = Column(String(50))
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    is_read = Column(Integer, default=0)  # Legacy field (use NotificationRead table)

    __table_args__ = (
        Index('idx_notif_user', 'user_id'),
        Index('idx_notif_type', 'notification_type'),
        Index('idx_notif_user_type', 'user_id', 'notification_type'),
        Index('idx_notif_created', 'created_at'),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.notification_type})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'notification_type': self.notification_type,
            'title': self.title,
            'message': self.message,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'priority': self.priority,
            'is_read': bool(self.is_read),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
