from datetime import datetime
from typing import List, Dict, Any
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


def get_unread_count(user_id: str, all_ids: list = None) -> int:
    """Get count of unread notifications for a user.

    If all_ids is provided, counts how many of those IDs are NOT read by user.
    Otherwise falls back to total - read count.
    """
    with SessionLocal() as session:
        read_ids = session.query(NotificationRead.notification_id).filter(
            NotificationRead.user_id == user_id
        ).all()
        read_id_set = {str(r[0]) for r in read_ids}

        if all_ids is not None:
            return sum(1 for aid in all_ids if str(aid) not in read_id_set)

        total = session.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id
        ).scalar() or 0

        return max(0, total - len(read_id_set))


def get_read_notification_ids(user_id: str) -> set:
    """Get set of notification IDs already read by user."""
    with SessionLocal() as session:
        read_ids = session.query(NotificationRead.notification_id).filter(
            NotificationRead.user_id == user_id
        ).all()
        return {str(r[0]) for r in read_ids}


def mark_notification_read(notification_id: str, user_id: str) -> bool:
    """Mark a specific notification as read. Returns True if it was unread."""
    with SessionLocal() as session:
        existing = session.query(NotificationRead).filter(
            and_(
                NotificationRead.user_id == user_id,
                NotificationRead.notification_id == str(notification_id)
            )
        ).first()

        if existing:
            return False

        read_record = NotificationRead(
            user_id=user_id,
            notification_id=str(notification_id),
            read_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(read_record)
        session.commit()
        return True


def mark_all_notifications_read(user_id: str, notification_ids: list) -> int:
    """Mark multiple notifications as read. Returns count of newly marked."""
    marked_count = 0
    with SessionLocal() as session:
        for nid in notification_ids:
            existing = session.query(NotificationRead).filter(
                and_(
                    NotificationRead.user_id == user_id,
                    NotificationRead.notification_id == str(nid)
                )
            ).first()

            if not existing:
                read_record = NotificationRead(
                    user_id=user_id,
                    notification_id=str(nid),
                    read_at=datetime.now(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(read_record)
                marked_count += 1

        session.commit()
    return marked_count
