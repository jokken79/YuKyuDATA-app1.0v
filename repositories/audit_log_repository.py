"""AuditLog Repository - Audit Trail Access"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from orm.models.audit_log import AuditLog
from repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for audit logs."""

    def __init__(self, session: Session):
        super().__init__(session, AuditLog)

    def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs by user."""
        return self.session.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def get_by_action(
        self,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs by action."""
        return self.session.query(AuditLog).filter(
            AuditLog.action == action
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def get_by_table(
        self,
        table_name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs for a table."""
        return self.session.query(AuditLog).filter(
            AuditLog.table_name == table_name
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def get_by_record(
        self,
        table_name: str,
        record_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get all audit logs for a specific record."""
        return self.session.query(AuditLog).filter(
            and_(
                AuditLog.table_name == table_name,
                AuditLog.record_id == record_id
            )
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def get_by_user_and_action(
        self,
        user_id: str,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs by user and action."""
        return self.session.query(AuditLog).filter(
            and_(
                AuditLog.user_id == user_id,
                AuditLog.action == action
            )
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def log_action(
        self,
        user_id: str,
        action: str,
        table_name: str,
        record_id: str,
        old_values: Optional[str] = None,
        new_values: Optional[str] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.session.add(log)
        self.session.flush()
        return log

    def get_recent(self, days: int = 7, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs (last N days)."""
        from datetime import datetime, timedelta, timezone
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        return self.session.query(AuditLog).filter(
            AuditLog.created_at >= start_date
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()

    def purge_older_than(self, days: int = 90) -> int:
        """Delete audit logs older than N days."""
        from datetime import datetime, timedelta, timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        count = self.session.query(AuditLog).filter(
            AuditLog.created_at < cutoff_date
        ).delete()
        self.session.flush()
        return count

    def count_by_action(self, action: str) -> int:
        """Count audit logs by action."""
        return self.session.query(AuditLog).filter(
            AuditLog.action == action
        ).count()

    def get_high_risk_actions(self, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Get high-risk actions (delete, update permissions, etc)."""
        risk_actions = ['delete', 'admin_grant', 'password_reset', 'config_change']
        return self.session.query(AuditLog).filter(
            AuditLog.action.in_(risk_actions)
        ).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
