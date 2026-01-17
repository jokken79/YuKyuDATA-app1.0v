"""
Models Package - Centralized Pydantic Schemas
Modelos Pydantic centralizados para YuKyuDATA

Este paquete contiene todos los schemas Pydantic del proyecto organizados
por dominio para facilitar su reutilizacion y mantenimiento.

Usage:
    from models import EmployeeUpdate, LeaveRequestCreate, APIResponse

    # O importar modulos especificos
    from models.employee import EmployeeUpdate, BulkUpdateRequest
    from models.leave_request import LeaveRequestCreate, LeaveRequestStatus
"""

# ============================================
# COMMON MODELS
# ============================================
from .common import (
    APIResponse,
    ErrorResponse,
    PaginatedResponse,
    PaginationInfo,
    PaginationParams,
    DateRangeQuery,
    StatusResponse,
    YearFilter,
)

# ============================================
# EMPLOYEE MODELS
# ============================================
from .employee import (
    EmployeeStatus,
    EmployeeType,
    EmployeeBase,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    BulkUpdateRequest,
    BulkUpdatePreview,
    BulkUpdateResult,
    EmployeeListResponse,
    EmployeeSearchRequest,
)

# ============================================
# LEAVE REQUEST MODELS
# ============================================
from .leave_request import (
    LeaveRequestStatus,
    LeaveType,
    LeaveRequestBase,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    LeaveRequestResponse,
    LeaveRequestApprove,
    LeaveRequestReject,
    LeaveRequestRevert,
    LeaveRequestFilter,
    LeaveRequestListResponse,
)

# ============================================
# VACATION (YUKYU) MODELS
# ============================================
from .vacation import (
    UsageDetailBase,
    UsageDetailCreate,
    UsageDetailUpdate,
    UsageDetailResponse,
    YukyuSummary,
    BalanceBreakdown,
    BalanceBreakdownResponse,
    MonthlySummary,
    YearlyUsageSummary,
    YukyuHistoryRecord,
)

# ============================================
# NOTIFICATION MODELS
# ============================================
from .notification import (
    NotificationType,
    NotificationPriority,
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    MarkAllNotificationsReadRequest,
    TestEmailRequest,
    NotificationListResponse,
    UnreadCountResponse,
)

# ============================================
# USER/AUTH MODELS
# ============================================
from .user import (
    UserRole,
    UserLogin,
    LoginRequest,
    RefreshRequest,
    RevokeRequest,
    UserBase,
    UserCreate,
    RegisterRequest,
    UserUpdate,
    UserResponse,
    ChangePasswordRequest,
    ResetPasswordRequest,
    SetPasswordRequest,
    TokenResponse,
    TokenPair,
    TokenData,
    CurrentUser,
)

# ============================================
# FISCAL YEAR MODELS
# ============================================
from .fiscal import (
    FiscalConfig,
    GrantTable,
    LifoDeductionRequest,
    LifoDeductionResult,
    CarryoverRequest,
    CarryoverResult,
    ComplianceCheckResult,
    ComplianceSummary,
    ExpiringSoonResult,
    ExpiringSoonSummary,
    GrantRecommendation,
)

# ============================================
# REPORT MODELS
# ============================================
from .report import (
    CustomReportRequest,
    MonthlyReportRequest,
    AnnualReportRequest,
    ReportMetadata,
    ReportListResponse,
    ReportGenerateResponse,
    ReportSummaryStats,
    MonthlyBreakdown,
    DepartmentBreakdown,
    CustomReportData,
    CreateIssueRequest,
    CommentRequest,
)

# ============================================
# VERSION INFO
# ============================================
__version__ = "1.0.0"
__author__ = "YuKyuDATA Team"

# ============================================
# ALL EXPORTS
# ============================================
__all__ = [
    # Common
    'APIResponse',
    'ErrorResponse',
    'PaginatedResponse',
    'PaginationInfo',
    'PaginationParams',
    'DateRangeQuery',
    'StatusResponse',
    'YearFilter',

    # Employee
    'EmployeeStatus',
    'EmployeeType',
    'EmployeeBase',
    'EmployeeCreate',
    'EmployeeUpdate',
    'EmployeeResponse',
    'BulkUpdateRequest',
    'BulkUpdatePreview',
    'BulkUpdateResult',
    'EmployeeListResponse',
    'EmployeeSearchRequest',

    # Leave Request
    'LeaveRequestStatus',
    'LeaveType',
    'LeaveRequestBase',
    'LeaveRequestCreate',
    'LeaveRequestUpdate',
    'LeaveRequestResponse',
    'LeaveRequestApprove',
    'LeaveRequestReject',
    'LeaveRequestRevert',
    'LeaveRequestFilter',
    'LeaveRequestListResponse',

    # Vacation (Yukyu)
    'UsageDetailBase',
    'UsageDetailCreate',
    'UsageDetailUpdate',
    'UsageDetailResponse',
    'YukyuSummary',
    'BalanceBreakdown',
    'BalanceBreakdownResponse',
    'MonthlySummary',
    'YearlyUsageSummary',
    'YukyuHistoryRecord',

    # Notification
    'NotificationType',
    'NotificationPriority',
    'NotificationBase',
    'NotificationCreate',
    'NotificationResponse',
    'NotificationSettingsUpdate',
    'NotificationSettingsResponse',
    'MarkAllNotificationsReadRequest',
    'TestEmailRequest',
    'NotificationListResponse',
    'UnreadCountResponse',

    # User/Auth
    'UserRole',
    'UserLogin',
    'LoginRequest',
    'RefreshRequest',
    'RevokeRequest',
    'UserBase',
    'UserCreate',
    'RegisterRequest',
    'UserUpdate',
    'UserResponse',
    'ChangePasswordRequest',
    'ResetPasswordRequest',
    'SetPasswordRequest',
    'TokenResponse',
    'TokenPair',
    'TokenData',
    'CurrentUser',

    # Fiscal
    'FiscalConfig',
    'GrantTable',
    'LifoDeductionRequest',
    'LifoDeductionResult',
    'CarryoverRequest',
    'CarryoverResult',
    'ComplianceCheckResult',
    'ComplianceSummary',
    'ExpiringSoonResult',
    'ExpiringSoonSummary',
    'GrantRecommendation',

    # Report
    'CustomReportRequest',
    'MonthlyReportRequest',
    'AnnualReportRequest',
    'ReportMetadata',
    'ReportListResponse',
    'ReportGenerateResponse',
    'ReportSummaryStats',
    'MonthlyBreakdown',
    'DepartmentBreakdown',
    'CustomReportData',
    'CreateIssueRequest',
    'CommentRequest',
]
