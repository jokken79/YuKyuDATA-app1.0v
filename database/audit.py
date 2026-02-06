from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from orm import SessionLocal, AuditLog


def log_audit_action(
    user_id: str = None,
    action: str = None,
    entity_type: str = None,
    entity_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    additional_info: Optional[str] = None
):
    """Log an action to the audit log using ORM."""
    with SessionLocal() as session:
        log_entry = AuditLog(
            user_id=user_id,
            action=action or '',
            table_name=entity_type or '',
            record_id=entity_id or '',
            old_values=str(old_value) if old_value else None,
            new_values=str(new_value) if new_value else None,
            reason=str(additional_info) if additional_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        session.add(log_entry)
        session.commit()
        return log_entry.id


def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Retrieve audit logs with optional filters."""
    with SessionLocal() as session:
        query = session.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.table_name == entity_type)
        if entity_id:
            query = query.filter(AuditLog.record_id == entity_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(AuditLog.created_at >= start_dt)
            except (ValueError, TypeError):
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(AuditLog.created_at <= end_dt)
            except (ValueError, TypeError):
                pass

        logs = query.order_by(
            AuditLog.created_at.desc()
        ).offset(offset).limit(limit).all()
        return [log.to_dict() for log in logs]


def get_audit_stats() -> Dict[str, Any]:
    """Get audit log statistics."""
    with SessionLocal() as session:
        total_entries = session.query(func.count(AuditLog.id)).scalar() or 0

        actions = session.query(
            AuditLog.action,
            func.count(AuditLog.id)
        ).group_by(AuditLog.action).all()

        tables = session.query(
            AuditLog.table_name,
            func.count(AuditLog.id)
        ).group_by(AuditLog.table_name).all()

        cutoff = datetime.now() - timedelta(hours=24)
        recent_count = session.query(func.count(AuditLog.id)).filter(
            AuditLog.created_at >= cutoff
        ).scalar() or 0

        return {
            'total_entries': total_entries,
            'recent_24h': recent_count,
            'by_action': {a: c for a, c in actions if a},
            'by_table': {t: c for t, c in tables if t},
        }


def cleanup_audit_log(days_to_keep: int = 90) -> int:
    """Delete audit log entries older than days_to_keep."""
    cutoff = datetime.now() - timedelta(days=days_to_keep)

    with SessionLocal() as session:
        count = session.query(AuditLog).filter(
            AuditLog.created_at < cutoff
        ).delete()
        session.commit()
        return count
