"""Notification Repository - Notification Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from orm.models.notification import Notification
from orm.models.notification_read import NotificationRead
from repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repository for notifications."""

    def __init__(self, session: Session):
        super().__init__(session, Notification)

    def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """Get notifications for user."""
        return self.session.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def get_unread_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """Get unread notifications for user."""
        return self.session.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == 0
            )
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def count_unread_by_user(self, user_id: str) -> int:
        """Count unread notifications for user."""
        return self.session.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == 0
            )
        ).count()

    def mark_as_read(self, id: str) -> Optional[Notification]:
        """Mark notification as read."""
        notification = self.get_by_id(id)
        if notification:
            notification.is_read = 1
            self.session.flush()
        return notification

    def mark_all_as_read_for_user(self, user_id: str) -> int:
        """Mark all notifications as read for user."""
        count = self.session.query(Notification).filter(
            Notification.user_id == user_id
        ).update({'is_read': 1})
        self.session.flush()
        return count

    def get_by_type(
        self,
        user_id: str,
        notification_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """Get notifications by type."""
        return self.session.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.notification_type == notification_type
            )
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_priority(
        self,
        user_id: str,
        priority: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """Get notifications by priority."""
        return self.session.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.priority == priority
            )
        ).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    def mark_read_for_user(self, user_id: str, notification_id: str) -> bool:
        """Mark specific notification as read for user using NotificationRead."""
        try:
            # Create or update NotificationRead record
            from datetime import datetime
            read_record = self.session.query(NotificationRead).filter(
                and_(
                    NotificationRead.user_id == user_id,
                    NotificationRead.notification_id == notification_id
                )
            ).first()

            if not read_record:
                read_record = NotificationRead(
                    user_id=user_id,
                    notification_id=notification_id,
                    read_at=datetime.utcnow()
                )
                self.session.add(read_record)

            self.session.flush()
            return True
        except:
            return False

    def is_read_by_user(self, user_id: str, notification_id: str) -> bool:
        """Check if notification has been read by user."""
        result = self.session.query(NotificationRead).filter(
            and_(
                NotificationRead.user_id == user_id,
                NotificationRead.notification_id == notification_id
            )
        ).first()
        return result is not None
