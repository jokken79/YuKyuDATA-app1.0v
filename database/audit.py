from datetime import datetime
from typing import List, Dict, Any, Optional
from orm import SessionLocal, AuditLog

def log_audit_action(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    additional_info: Optional[str] = None
):
    """Log an action to the audit log using ORM"""
    with SessionLocal() as session:
        log_entry = AuditLog(
            timestamp=datetime.now(),
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_info=str(additional_info) if additional_info else None
        )
        session.add(log_entry)
        session.commit()

def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Retrieve audit logs using ORM"""
    with SessionLocal() as session:
        query = session.query(AuditLog)
        
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == entity_id)
            
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        return [log.to_dict() for log in logs]
