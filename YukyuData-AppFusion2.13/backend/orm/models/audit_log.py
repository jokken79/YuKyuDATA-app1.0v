"""AuditLog ORM Model - Complete Audit Trail"""

from sqlalchemy import Column, String, Index
from orm.models.base import Base, BaseModel


class AuditLog(BaseModel, Base):
    """
    Complete audit trail for all data modifications.

    Tracks who did what, when, and what changed for compliance and debugging.

    Attributes:
        id: UUID primary key
        user_id: User who made the change (indexed)
        action: Type of action (create, update, delete, approve, reject, revert)
        table_name: Name of affected table (indexed)
        record_id: ID of affected record (indexed)
        old_values: JSON string of previous values
        new_values: JSON string of new values
        reason: Reason for change (optional)
        ip_address: IP address of request source
        user_agent: User agent of request
        created_at: Timestamp of change (indexed)
    """

    __tablename__ = "audit_log"

    user_id = Column(String(50), index=True)
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, approve, reject
    table_name = Column(String(50), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    old_values = Column(String(5000))  # JSON string
    new_values = Column(String(5000))  # JSON string
    reason = Column(String(500))
    ip_address = Column(String(45))  # Support IPv4 and IPv6
    user_agent = Column(String(500))

    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_table', 'table_name'),
        Index('idx_audit_record', 'record_id'),
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_created', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, table={self.table_name})>"

    def to_dict(self):
        """Convert to dict for API responses."""
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'old_values': json.loads(self.old_values) if self.old_values else None,
            'new_values': json.loads(self.new_values) if self.new_values else None,
            'reason': self.reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
