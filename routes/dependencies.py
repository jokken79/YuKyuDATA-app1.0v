"""
Shared Dependencies for API Routes
Dependencias compartidas para todos los routers
"""

from fastapi import Depends, HTTPException, Request, Query
from typing import Optional
from pathlib import Path
from datetime import datetime

# Import authentication dependencies
from auth import (
    get_current_user,
    get_admin_user,
    check_rate_limit,
    CurrentUser
)

# Import database module
import database

# Import services
from services.search_service import SearchService

# Import logging
from logger import logger, log_api_request, log_db_operation, log_sync_event, log_leave_request

# Import caching
from caching import cached, invalidate_employee_cache, get_cache_stats

# Import fiscal year utilities
from fiscal_year import (
    process_year_end_carryover,
    get_employee_balance_breakdown,
    check_expiring_soon,
    check_5day_compliance,
    get_grant_recommendation,
    calculate_seniority_years,
    calculate_granted_days,
    get_fiscal_period,
    apply_lifo_deduction,
    FISCAL_CONFIG,
    GRANT_TABLE
)

# Import CSRF utilities
from csrf_middleware import generate_csrf_token

# Project paths
PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_EXCEL_PATH = PROJECT_DIR / "有給休暇管理.xlsm"
EMPLOYEE_REGISTRY_PATH = PROJECT_DIR / "【新】社員台帳(UNS)T　2022.04.05～.xlsm"
UPLOAD_DIR = PROJECT_DIR / "uploads"


def get_client_info(request: Request) -> dict:
    """
    Extract client information from FastAPI Request.
    Extrae informacion del cliente desde el Request de FastAPI.
    """
    client_ip = request.client.host if request.client else None

    # Try to get real IP if behind proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent", "")

    return {
        "ip_address": client_ip,
        "user_agent": user_agent[:500] if user_agent else None
    }


async def log_audit_action(
    request: Request,
    action: str,
    entity_type: str,
    entity_id: str = None,
    old_value=None,
    new_value=None,
    user=None,
    additional_info: dict = None
):
    """
    Helper function to manually log an action in the audit log.
    Funcion auxiliar para registrar manualmente una accion en el audit log.
    """
    client_info = get_client_info(request)

    user_id = None
    if user:
        if hasattr(user, 'username'):
            user_id = user.username
        elif isinstance(user, dict):
            user_id = user.get('username')

    try:
        audit_id = database.log_audit(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            old_value=old_value,
            new_value=new_value,
            user_id=user_id,
            ip_address=client_info.get('ip_address'),
            user_agent=client_info.get('user_agent'),
            additional_info=additional_info
        )
        return audit_id
    except Exception as e:
        logger.warning(f"Failed to log audit: {str(e)}")
        return None


def get_active_employee_nums() -> set:
    """
    Get employee numbers for ACTIVE employees (status = '在職中').
    Obtiene los numeros de empleados ACTIVOS (status = '在職中').
    """
    active_nums = set()

    # Active employees from genzai (dispatch)
    genzai = database.get_genzai(status='在職中')
    for emp in genzai:
        if emp.get('employee_num'):
            active_nums.add(str(emp['employee_num']))

    # Active employees from ukeoi (contract)
    ukeoi = database.get_ukeoi(status='在職中')
    for emp in ukeoi:
        if emp.get('employee_num'):
            active_nums.add(str(emp['employee_num']))

    return active_nums


# Re-export commonly used items
__all__ = [
    # Auth dependencies
    'get_current_user',
    'get_admin_user',
    'check_rate_limit',
    'CurrentUser',
    # Database
    'database',
    # Search
    'SearchService',
    # Logging
    'logger',
    'log_api_request',
    'log_db_operation',
    'log_sync_event',
    'log_leave_request',
    # Caching
    'cached',
    'invalidate_employee_cache',
    'get_cache_stats',
    # Fiscal year
    'FISCAL_CONFIG',
    'GRANT_TABLE',
    'check_5day_compliance',
    'check_expiring_soon',
    'get_employee_balance_breakdown',
    'get_grant_recommendation',
    'apply_lifo_deduction',
    'process_year_end_carryover',
    # Helpers
    'get_client_info',
    'log_audit_action',
    'get_active_employee_nums',
    # Paths
    'PROJECT_DIR',
    'DEFAULT_EXCEL_PATH',
    'EMPLOYEE_REGISTRY_PATH',
    'UPLOAD_DIR',
    # CSRF
    'generate_csrf_token',
]
