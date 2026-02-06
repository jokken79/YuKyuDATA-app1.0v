from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_
from orm import SessionLocal, Notification, NotificationRead

def create_notification(user_id: str, title: str, message: str, type: str = 'info') -> Dict[str, Any]:
    """Create a new notification using ORM."""
    with SessionLocal() as session:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(notif)
        session.commit()
        session.refresh(notif)
        return notif.to_dict()

def get_notifications(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get notifications for a user, enriched with read status."""
    with SessionLocal() as session:
        # Get notification IDs already read by user
        read_ids = session.query(NotificationRead.notification_id).filter(
            NotificationRead.user_id == user_id
        ).all()
        read_id_set = {r[0] for r in read_ids}
        
        notifications = session.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(limit).all()
        
        result = []
        for n in notifications:
            n_dict = n.to_dict()
            n_dict['is_read'] = n.id in read_id_set
            result.append(n_dict)
            
        return result

def mark_notification_as_read(user_id: str, notification_id: int):
    """Mark a notification as read using ORM."""
    with SessionLocal() as session:
        # Check if already read
        existing = session.query(NotificationRead).filter(
            and_(
                NotificationRead.user_id == user_id,
                NotificationRead.notification_id == notification_id
            )
        ).first()
        
        if not existing:
            read_record = NotificationRead(
                user_id=user_id,
                notification_id=notification_id,
                read_at=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(read_record)
            session.commit()

def get_unread_count(user_id: str) -> int:
    """Get count of unread notifications for a user."""
    with SessionLocal() as session:
        total = session.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id
        ).scalar() or 0
        
        read_count = session.query(func.count(NotificationRead.id)).filter(
            NotificationRead.user_id == user_id
        ).scalar() or 0
        
        return max(0, total - read_count)
