"""
Services Module
Contiene la logica de negocio separada de los endpoints
"""

# Auth - exported from auth.py
from .auth import (
    create_access_token,
    verify_token,
    authenticate_user,
    get_current_user,
    get_admin_user,
    check_rate_limit,
    hash_password,
    verify_password,
    get_token_from_header,
    log_auth_event,
    CurrentUser,
    UserLogin,
    TokenResponse,
)

# Auth Service
from .auth_service import AuthService

# Fiscal Year
from .fiscal_year import (
    process_year_end_carryover,
    get_employee_balance_breakdown,
    check_expiring_soon,
    check_5day_compliance,
    get_grant_recommendation,
    calculate_seniority_years,
    calculate_granted_days,
    get_fiscal_period,
    get_fiscal_year_period,
    apply_lifo_deduction,
    apply_fifo_deduction,
    FISCAL_CONFIG,
    GRANT_TABLE,
)

# Notifications
from .notifications import (
    NotificationService,
    NotificationSettings,
    NotificationLog,
)

# Reports
from .reports import (
    ReportGenerator,
    save_report,
    list_reports,
    cleanup_old_reports,
    REPORTS_DIR,
)

# Excel Service - import the module for `import excel_service` style usage
from . import excel_service

# Excel Export
from .excel_export import (
    create_approved_requests_excel,
    create_monthly_report_excel,
    create_annual_ledger_excel,
    update_master_excel,
    get_export_files,
    cleanup_old_exports,
    EXPORT_DIR,
)

# Caching
from .caching import (
    cached,
    invalidate_employee_cache,
    get_cache_stats,
    clear_cache,
    invalidate_cache_pattern,
    invalidate_genzai_cache,
    invalidate_ukeoi_cache,
    invalidate_stats_cache,
    SimpleCache,
)

# Crypto Utils
from .crypto_utils import (
    encrypt_field,
    decrypt_field,
    get_encryption_manager,
)

# Search Service
from .search_service import SearchService

# Asset Service
from .asset_service import AssetService

__all__ = [
    # Auth
    "create_access_token",
    "verify_token",
    "authenticate_user",
    "get_current_user",
    "get_admin_user",
    "check_rate_limit",
    "hash_password",
    "verify_password",
    "get_token_from_header",
    "log_auth_event",
    "CurrentUser",
    "UserLogin",
    "TokenResponse",
    "AuthService",
    # Fiscal Year
    "process_year_end_carryover",
    "get_employee_balance_breakdown",
    "check_expiring_soon",
    "check_5day_compliance",
    "get_grant_recommendation",
    "calculate_seniority_years",
    "calculate_granted_days",
    "get_fiscal_period",
    "get_fiscal_year_period",
    "apply_lifo_deduction",
    "apply_fifo_deduction",
    "FISCAL_CONFIG",
    "GRANT_TABLE",
    # Notifications
    "NotificationService",
    "NotificationSettings",
    "NotificationLog",
    # Reports
    "ReportGenerator",
    "save_report",
    "list_reports",
    "cleanup_old_reports",
    "REPORTS_DIR",
    # Excel Service
    "excel_service",
    # Excel Export
    "create_approved_requests_excel",
    "create_monthly_report_excel",
    "create_annual_ledger_excel",
    "update_master_excel",
    "get_export_files",
    "cleanup_old_exports",
    "EXPORT_DIR",
    # Caching
    "cached",
    "invalidate_employee_cache",
    "get_cache_stats",
    "clear_cache",
    "invalidate_cache_pattern",
    "invalidate_genzai_cache",
    "invalidate_ukeoi_cache",
    "invalidate_stats_cache",
    "SimpleCache",
    # Crypto Utils
    "encrypt_field",
    "decrypt_field",
    "get_encryption_manager",
    # Services
    "SearchService",
    "AssetService",
]
