"""
Vacation Models (Yukyu) - Schemas de vacaciones
Modelos Pydantic para gestion de uso de vacaciones y detalles
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


# ============================================
# USAGE DETAIL MODELS
# ============================================

class UsageDetailBase(BaseModel):
    """Campos base para detalles de uso de vacaciones."""
    employee_num: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Numero de empleado"
    )
    use_date: str = Field(
        ...,
        description="Fecha de uso YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    days_used: float = Field(
        1.0,
        ge=0.25,
        le=1.0,
        description="Dias usados (0.25, 0.5, 0.75, 1.0)"
    )


class UsageDetailCreate(UsageDetailBase):
    """Modelo para crear un nuevo registro de uso de vacaciones."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre del empleado"
    )

    @field_validator('days_used')
    @classmethod
    def validate_days(cls, v):
        valid_values = [0.25, 0.5, 0.75, 1.0]
        if v not in valid_values:
            raise ValueError(f'days_used debe ser: {valid_values} (0.5 = medio dia)')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "name": "Taro Yamada",
                "use_date": "2025-01-20",
                "days_used": 1.0
            }
        }
    )


class UsageDetailUpdate(BaseModel):
    """Modelo para actualizar un registro de uso de vacaciones."""
    days_used: Optional[float] = Field(
        None,
        ge=0.25,
        le=1.0,
        description="Dias usados (0.25, 0.5, 0.75, 1.0)"
    )
    use_date: Optional[str] = Field(
        None,
        description="Nueva fecha YYYY-MM-DD",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )

    @field_validator('days_used')
    @classmethod
    def validate_days(cls, v):
        if v is not None:
            valid_values = [0.25, 0.5, 0.75, 1.0]
            if v not in valid_values:
                raise ValueError(f'days_used debe ser: {valid_values} (0.5 = medio dia)')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "days_used": 0.5,
                "use_date": "2025-01-21"
            }
        }
    )


class UsageDetailResponse(BaseModel):
    """Modelo de respuesta para detalle de uso."""
    id: int = Field(..., description="ID del registro")
    employee_num: str = Field(..., description="Numero de empleado")
    name: Optional[str] = Field(None, description="Nombre del empleado")
    use_date: str = Field(..., description="Fecha de uso")
    days_used: float = Field(..., description="Dias usados")
    year: int = Field(..., description="Ano fiscal")
    month: int = Field(..., description="Mes")
    source: Optional[str] = Field(None, description="Fuente del registro")
    created_at: Optional[datetime] = Field(None, description="Fecha de creacion")
    updated_at: Optional[datetime] = Field(None, description="Fecha de actualizacion")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "employee_num": "001",
                "name": "Taro Yamada",
                "use_date": "2025-01-20",
                "days_used": 1.0,
                "year": 2025,
                "month": 1,
                "source": "manual"
            }
        }
    )


# ============================================
# SUMMARY MODELS
# ============================================

class YukyuSummary(BaseModel):
    """Resumen de vacaciones de un empleado."""
    employee_num: str = Field(..., description="Numero de empleado")
    name: Optional[str] = Field(None, description="Nombre")
    year: int = Field(..., description="Ano fiscal")
    granted: float = Field(0, description="Dias otorgados")
    used: float = Field(0, description="Dias usados")
    balance: float = Field(0, description="Saldo disponible")
    expired: float = Field(0, description="Dias expirados")
    usage_rate: float = Field(0, description="Tasa de uso (%)")
    days_until_expiry: Optional[int] = Field(None, description="Dias hasta expiracion")
    compliant_5day: bool = Field(False, description="Cumple con 5 dias obligatorios")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "name": "Taro Yamada",
                "year": 2025,
                "granted": 15,
                "used": 6,
                "balance": 9,
                "expired": 0,
                "usage_rate": 40.0,
                "days_until_expiry": 180,
                "compliant_5day": True
            }
        }
    )


class BalanceBreakdown(BaseModel):
    """Desglose del balance por ano de otorgamiento."""
    grant_year: int = Field(..., description="Ano de otorgamiento")
    original_granted: float = Field(..., description="Dias otorgados originalmente")
    used_from_this_grant: float = Field(0, description="Dias usados de este otorgamiento")
    remaining: float = Field(..., description="Dias restantes")
    expiry_date: Optional[str] = Field(None, description="Fecha de expiracion")
    is_expired: bool = Field(False, description="Si ya expiro")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "grant_year": 2024,
                "original_granted": 10,
                "used_from_this_grant": 5,
                "remaining": 5,
                "expiry_date": "2026-03-20",
                "is_expired": False
            }
        }
    )


class BalanceBreakdownResponse(BaseModel):
    """Respuesta con desglose completo del balance."""
    employee_num: str = Field(..., description="Numero de empleado")
    year: int = Field(..., description="Ano actual")
    total_balance: float = Field(..., description="Balance total")
    breakdown: List[BalanceBreakdown] = Field(..., description="Desglose por ano")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "year": 2025,
                "total_balance": 15,
                "breakdown": [
                    {
                        "grant_year": 2024,
                        "original_granted": 10,
                        "used_from_this_grant": 5,
                        "remaining": 5,
                        "expiry_date": "2026-03-20",
                        "is_expired": False
                    }
                ]
            }
        }
    )


# ============================================
# MONTHLY SUMMARY
# ============================================

class MonthlySummary(BaseModel):
    """Resumen mensual de uso de vacaciones."""
    month: int = Field(..., ge=1, le=12, description="Mes (1-12)")
    year: int = Field(..., description="Ano")
    total_days_used: float = Field(0, description="Total dias usados")
    employee_count: int = Field(0, description="Empleados que usaron vacaciones")
    requests_count: int = Field(0, description="Numero de solicitudes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month": 1,
                "year": 2025,
                "total_days_used": 45.5,
                "employee_count": 20,
                "requests_count": 25
            }
        }
    )


class YearlyUsageSummary(BaseModel):
    """Resumen anual de uso de vacaciones."""
    year: int = Field(..., description="Ano fiscal")
    monthly_data: List[MonthlySummary] = Field(..., description="Datos mensuales")
    total_days_used: float = Field(0, description="Total dias usados en el ano")
    total_days_granted: float = Field(0, description="Total dias otorgados")
    overall_usage_rate: float = Field(0, description="Tasa de uso global (%)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 2025,
                "monthly_data": [],
                "total_days_used": 250.5,
                "total_days_granted": 500,
                "overall_usage_rate": 50.1
            }
        }
    )


# ============================================
# HISTORY MODEL
# ============================================

class YukyuHistoryRecord(BaseModel):
    """Registro historico de vacaciones."""
    year: int = Field(..., description="Ano fiscal")
    granted: float = Field(0, description="Dias otorgados")
    used: float = Field(0, description="Dias usados")
    balance: float = Field(0, description="Saldo")
    expired: float = Field(0, description="Dias expirados")
    carried_over: float = Field(0, description="Dias traspasados")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 2024,
                "granted": 12,
                "used": 10,
                "balance": 2,
                "expired": 0,
                "carried_over": 2
            }
        }
    )


# Export all
__all__ = [
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
]
