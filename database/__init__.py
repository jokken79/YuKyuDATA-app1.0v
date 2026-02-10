from .connection import get_db, USE_POSTGRESQL
from .init_db import init_db

# Employees (vacation data)
from .employees import (
    save_employees,
    save_employee_data,
    get_employees,
    get_employees_enhanced,
    get_available_years,
    get_employee_by_num_year,
    update_employee,
    reset_employees,
    get_employee_yukyu_history,
    get_employee_total_balance,
    get_employee_usage_summary,
    get_employee_hourly_wage,
    recalculate_employee_from_details,
    bulk_update_employees,
    get_bulk_update_history,
    revert_bulk_update,
)

# Genzai (dispatch employees)
from .genzai import get_genzai, save_genzai, reset_genzai

# Ukeoi (contract employees)
from .ukeoi import get_ukeoi, save_ukeoi, reset_ukeoi

# Staff (office employees)
from .staff import get_staff, save_staff, reset_staff

# Leave requests
from .leave import (
    save_leave_request,
    get_leave_requests,
    save_yukyu_usage_details,
    create_leave_request,
    approve_leave_request,
    reject_leave_request,
    cancel_leave_request,
    validate_balance_limit,
    revert_approved_request,
)

# Yukyu usage details
from .yukyu import (
    get_yukyu_usage_details,
    get_usage_detail_by_id,
    create_yukyu_usage_detail,
    update_yukyu_usage_detail,
    delete_yukyu_usage_detail,
    get_monthly_usage_summary,
    reset_yukyu_usage_details,
)

# Audit
from .audit import log_audit_action, get_audit_logs, get_audit_stats, cleanup_audit_log

# Backup
from .backup import create_backup, list_backups, restore_backup

# Notifications
from .notifications import (
    create_notification,
    get_notifications,
    mark_notification_as_read,
    get_unread_count,
    get_read_notification_ids,
    mark_notification_read,
    mark_all_notifications_read,
)

# Refresh Tokens
from .refresh_tokens import (
    init_refresh_tokens_table,
    store_refresh_token,
    get_refresh_token_by_hash,
    revoke_refresh_token,
    revoke_all_user_refresh_tokens,
    is_refresh_token_valid,
    cleanup_expired_refresh_tokens,
    get_user_active_refresh_tokens,
    get_refresh_token_stats,
)

# CSRF Tokens
from .csrf_tokens import (
    init_csrf_tokens_table,
    store_csrf_token,
    validate_csrf_token,
    cleanup_expired_csrf_tokens,
    get_csrf_token_stats,
)

# Stats
from .stats import get_dashboard_stats, get_workplace_distribution, get_employee_type_distribution, get_table_counts

# Legacy aliases for backwards compatibility
log_action = log_audit_action
log_audit = log_audit_action
get_audit_log = get_audit_logs

__all__ = [
    # Connection
    'get_db',
    'USE_POSTGRESQL',
    'init_db',
    # Employees
    'save_employees',
    'save_employee_data',
    'get_employees',
    'get_employees_enhanced',
    'get_available_years',
    'get_employee_by_num_year',
    'update_employee',
    'reset_employees',
    'get_employee_yukyu_history',
    'get_employee_total_balance',
    'get_employee_usage_summary',
    'get_employee_hourly_wage',
    'recalculate_employee_from_details',
    'bulk_update_employees',
    'get_bulk_update_history',
    'revert_bulk_update',
    # Genzai
    'get_genzai',
    'save_genzai',
    'reset_genzai',
    # Ukeoi
    'get_ukeoi',
    'save_ukeoi',
    'reset_ukeoi',
    # Staff
    'get_staff',
    'save_staff',
    'reset_staff',
    # Leave requests
    'save_leave_request',
    'get_leave_requests',
    'save_yukyu_usage_details',
    'create_leave_request',
    'approve_leave_request',
    'reject_leave_request',
    'cancel_leave_request',
    'validate_balance_limit',
    'revert_approved_request',
    # Yukyu usage details
    'get_yukyu_usage_details',
    'get_usage_detail_by_id',
    'create_yukyu_usage_detail',
    'update_yukyu_usage_detail',
    'delete_yukyu_usage_detail',
    'get_monthly_usage_summary',
    'reset_yukyu_usage_details',
    # Audit
    'log_action',
    'log_audit',
    'log_audit_action',
    'get_audit_logs',
    'get_audit_log',
    'get_audit_stats',
    'cleanup_audit_log',
    # Backup
    'create_backup',
    'list_backups',
    'restore_backup',
    # Notifications
    'create_notification',
    'get_notifications',
    'mark_notification_as_read',
    'get_unread_count',
    'get_read_notification_ids',
    'mark_notification_read',
    'mark_all_notifications_read',
    # Refresh Tokens
    'init_refresh_tokens_table',
    'store_refresh_token',
    'get_refresh_token_by_hash',
    'revoke_refresh_token',
    'revoke_all_user_refresh_tokens',
    'is_refresh_token_valid',
    'cleanup_expired_refresh_tokens',
    'get_user_active_refresh_tokens',
    'get_refresh_token_stats',
    # Stats
    'get_dashboard_stats',
    'get_workplace_distribution',
    'get_employee_type_distribution',
    'get_table_counts',
]
