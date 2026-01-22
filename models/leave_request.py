"""
Leave Request Models - Schemas de solicitudes de vacaciones
Modelos Pydantic para el workflow de solicitudes
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class LeaveRequestStatus(str, Enum):
    """Estado de la solicitud de vacaciones."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LeaveType(str, Enum):
    """Tipo de licencia."""
    FULL = "full"          # Dia completo
    HALF_AM = "half_am"    # Medio dia manana
    HALF_PM = "half_pm"    # Medio dia tarde
    HOURLY = "hourly"      # Por horas


# ============================================
# BASE MODELS
# ============================================

class LeaveRequestBase(BaseModel):
    """Campos base para solicitudes de vacaciones."""
    employee_num: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Numero de empleado"
    )
    employee_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del empleado"
    )
    start_date: str = Field(
        ...,
        description="Fecha inicio YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: str = Field(
        ...,
        description="Fecha fin YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    leave_type: LeaveType = Field(
        LeaveType.FULL,
        description="Tipo de licencia: full, half_am, half_pm, hourly"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Motivo de la solicitud"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True
    )


class LeaveRequestCreate(LeaveRequestBase):
    """Modelo para crear una nueva solicitud de vacaciones."""
    days_requested: float = Field(
        ...,
        ge=0,
        le=40,
        description="Dias solicitados (0-40)"
    )
    hours_requested: float = Field(
        0,
        ge=0,
        le=320,
        description="Horas solicitadas (para tipo hourly)"
    )

    @field_validator('leave_type', mode='before')
    @classmethod
    def validate_leave_type(cls, v):
        valid_types = ['full', 'half_am', 'half_pm', 'hourly']
        if v not in valid_types:
            raise ValueError(f'leave_type debe ser uno de: {valid_types}')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError('end_date debe ser posterior a start_date')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "employee_name": "Taro Yamada",
                "start_date": "2025-02-01",
                "end_date": "2025-02-03",
                "days_requested": 3,
                "hours_requested": 0,
                "leave_type": "full",
                "reason": "Family vacation"
            }
        }
    )


class LeaveRequestUpdate(BaseModel):
    """Modelo para actualizar una solicitud existente."""
    start_date: Optional[str] = Field(
        None,
        description="Nueva fecha inicio YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    end_date: Optional[str] = Field(
        None,
        description="Nueva fecha fin YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    days_requested: Optional[float] = Field(None, ge=0, le=40)
    hours_requested: Optional[float] = Field(None, ge=0, le=320)
    leave_type: Optional[LeaveType] = None
    reason: Optional[str] = Field(None, max_length=500)


class LeaveRequestResponse(BaseModel):
    """Modelo de respuesta para solicitud de vacaciones."""
    id: int = Field(..., description="ID de la solicitud")
    employee_num: str = Field(..., description="Numero de empleado")
    employee_name: str = Field(..., description="Nombre del empleado")
    start_date: str = Field(..., description="Fecha inicio")
    end_date: str = Field(..., description="Fecha fin")
    days_requested: float = Field(..., description="Dias solicitados")
    hours_requested: float = Field(0, description="Horas solicitadas")
    leave_type: str = Field(..., description="Tipo de licencia")
    reason: Optional[str] = Field(None, description="Motivo")
    status: LeaveRequestStatus = Field(..., description="Estado de la solicitud")
    year: int = Field(..., description="Ano fiscal")
    hourly_wage: Optional[float] = Field(None, description="Salario por hora")
    approver: Optional[str] = Field(None, description="Usuario que aprobo/rechazo")
    approved_at: Optional[datetime] = Field(None, description="Fecha de aprobacion")
    rejection_reason: Optional[str] = Field(None, description="Motivo de rechazo")
    created_at: Optional[datetime] = Field(None, description="Fecha de creacion")

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "employee_num": "001",
                "employee_name": "Taro Yamada",
                "start_date": "2025-02-01",
                "end_date": "2025-02-03",
                "days_requested": 3.0,
                "hours_requested": 0,
                "leave_type": "full",
                "reason": "Family vacation",
                "status": "PENDING",
                "year": 2025,
                "hourly_wage": 1500,
                "approver": None,
                "approved_at": None,
                "created_at": "2025-01-17T10:00:00"
            }
        }
    )


# ============================================
# ACTION MODELS
# ============================================

class LeaveRequestApprove(BaseModel):
    """Modelo para aprobar una solicitud."""
    approved_by: Optional[str] = Field(
        None,
        max_length=100,
        description="Usuario que aprueba (si no se especifica, usa el usuario actual)"
    )
    validate_limit: bool = Field(
        True,
        description="Validar limite de balance antes de aprobar"
    )
    approver_comment: Optional[str] = Field(
        None,
        max_length=500,
        description="Comentario del aprobador"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "approved_by": "admin",
                "validate_limit": True,
                "approver_comment": "Approved as requested"
            }
        }
    )


class LeaveRequestReject(BaseModel):
    """Modelo para rechazar una solicitud."""
    rejection_reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Motivo del rechazo"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "rejection_reason": "Insufficient leave balance"
            }
        }
    )


class LeaveRequestRevert(BaseModel):
    """Modelo para revertir una solicitud aprobada."""
    revert_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Motivo de la reversion"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "revert_reason": "Employee cancelled the leave"
            }
        }
    )


# ============================================
# LIST/FILTER MODELS
# ============================================

class LeaveRequestFilter(BaseModel):
    """Modelo para filtrar solicitudes."""
    status: Optional[LeaveRequestStatus] = Field(None, description="Filtrar por estado")
    employee_num: Optional[str] = Field(None, description="Filtrar por empleado")
    year: Optional[int] = Field(None, ge=2000, le=2100, description="Filtrar por ano")
    leave_type: Optional[LeaveType] = Field(None, description="Filtrar por tipo")
    start_date_from: Optional[str] = Field(
        None,
        description="Fecha inicio desde",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    start_date_to: Optional[str] = Field(
        None,
        description="Fecha inicio hasta",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )

    model_config = ConfigDict(
        use_enum_values=True
    )


class LeaveRequestListResponse(BaseModel):
    """Respuesta para lista de solicitudes."""
    status: str = Field("success")
    data: List[LeaveRequestResponse] = Field(..., description="Lista de solicitudes")
    count: int = Field(..., description="Total de solicitudes")
    pending_count: Optional[int] = Field(None, description="Solicitudes pendientes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": [],
                "count": 10,
                "pending_count": 3
            }
        }
    )


# Export all
__all__ = [
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
]
