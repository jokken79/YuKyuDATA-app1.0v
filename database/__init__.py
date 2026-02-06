from .connection import get_db, USE_POSTGRESQL
from .init_db import init_db
from .employees import save_employees, save_employee_data, get_employees
from .leave import save_leave_request, get_leave_requests, save_yukyu_usage_details
from .audit import log_audit_action, get_audit_logs
from .notifications import create_notification, get_notifications, mark_notification_as_read, get_unread_count
from .stats import get_dashboard_stats, get_workplace_distribution, get_employee_type_distribution

# Legacy mapping for backwards compatibility
log_action = log_audit_action

__all__ = [
    'get_db', 
    'USE_POSTGRESQL', 
    'init_db',
    'save_employees', 
    'save_employee_data', 
    'get_employees',
    'save_leave_request', 
    'get_leave_requests', 
    'save_yukyu_usage_details',
    'log_action', 
    'log_audit_action', 
    'get_audit_logs',
    'create_notification', 
    'get_notifications', 
    'mark_notification_as_read', 
    'get_unread_count',
    'get_dashboard_stats', 
    'get_workplace_distribution', 
    'get_employee_type_distribution'
]
