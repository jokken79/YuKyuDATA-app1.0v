"""
Fiscal Year Models - Schemas del ano fiscal
Modelos Pydantic para operaciones del ano fiscal japones
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date


# ============================================
# FISCAL CONFIG
# ============================================

class FiscalConfig(BaseModel):
    """Configuracion del ano fiscal japones."""
    start_day: int = Field(21, ge=1, le=31, description="Dia de inicio del periodo")
    max_carryover_years: int = Field(2, ge=1, le=5, description="Anos maximos de carryover")
    max_accumulated_days: int = Field(40, ge=1, le=100, description="Dias maximos acumulados")
    min_required_days: int = Field(5, ge=0, le=40, description="Dias minimos obligatorios")
    min_granted_for_compliance: int = Field(
        10,
        ge=0,
        le=40,
        description="Dias minimos otorgados para aplicar compliance"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_day": 21,
                "max_carryover_years": 2,
                "max_accumulated_days": 40,
                "min_required_days": 5,
                "min_granted_for_compliance": 10
            }
        }
    )


class GrantTable(BaseModel):
    """Tabla de otorgamiento por antiguedad."""
    seniority_years: float = Field(..., description="Anos de antiguedad")
    granted_days: int = Field(..., description="Dias otorgados")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "seniority_years": 0.5,
                "granted_days": 10
            }
        }
    )


# ============================================
# LIFO DEDUCTION
# ============================================

class LifoDeductionRequest(BaseModel):
    """Request para deduccion LIFO (usa dias mas nuevos primero)."""
    employee_num: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Numero de empleado"
    )
    days: float = Field(
        ...,
        gt=0,
        le=40,
        description="Dias a deducir (1-40)"
    )
    year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Ano fiscal"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "days": 3,
                "year": 2025
            }
        }
    )


class LifoDeductionResult(BaseModel):
    """Resultado de la deduccion LIFO."""
    success: bool = Field(..., description="Si la deduccion fue exitosa")
    days_deducted: float = Field(..., description="Dias efectivamente deducidos")
    deductions_by_year: List[dict] = Field(
        ...,
        description="Desglose de deduccion por ano de otorgamiento"
    )
    remaining_balance: float = Field(..., description="Balance restante")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "days_deducted": 3,
                "deductions_by_year": [
                    {"grant_year": 2025, "deducted": 3}
                ],
                "remaining_balance": 12
            }
        }
    )


# ============================================
# CARRYOVER
# ============================================

class CarryoverRequest(BaseModel):
    """Request para traspaso de fin de ano."""
    from_year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Ano de origen"
    )
    to_year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Ano destino"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "from_year": 2024,
                "to_year": 2025
            }
        }
    )


class CarryoverResult(BaseModel):
    """Resultado del proceso de carryover."""
    success: bool = Field(..., description="Si el proceso fue exitoso")
    from_year: int = Field(..., description="Ano de origen")
    to_year: int = Field(..., description="Ano destino")
    employees_processed: int = Field(..., description="Empleados procesados")
    total_carried_over: float = Field(..., description="Total de dias traspasados")
    total_expired: float = Field(..., description="Total de dias expirados")
    details: Optional[List[dict]] = Field(None, description="Detalle por empleado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "from_year": 2024,
                "to_year": 2025,
                "employees_processed": 50,
                "total_carried_over": 150.5,
                "total_expired": 25
            }
        }
    )


# ============================================
# COMPLIANCE
# ============================================

class ComplianceCheckResult(BaseModel):
    """Resultado de verificacion de compliance de 5 dias."""
    employee_num: str = Field(..., description="Numero de empleado")
    name: Optional[str] = Field(None, description="Nombre")
    granted: float = Field(..., description="Dias otorgados")
    used: float = Field(..., description="Dias usados")
    required: float = Field(5, description="Dias requeridos")
    compliant: bool = Field(..., description="Si cumple con los 5 dias")
    days_remaining_to_comply: float = Field(
        0,
        description="Dias que faltan para cumplir"
    )
    days_until_deadline: Optional[int] = Field(
        None,
        description="Dias hasta el deadline"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "name": "Taro Yamada",
                "granted": 15,
                "used": 3,
                "required": 5,
                "compliant": False,
                "days_remaining_to_comply": 2,
                "days_until_deadline": 90
            }
        }
    )


class ComplianceSummary(BaseModel):
    """Resumen de compliance para un ano."""
    year: int = Field(..., description="Ano fiscal")
    total_employees: int = Field(..., description="Total empleados con 10+ dias")
    compliant_count: int = Field(..., description="Empleados que cumplen")
    non_compliant_count: int = Field(..., description="Empleados que no cumplen")
    compliance_rate: float = Field(..., description="Tasa de compliance (%)")
    non_compliant_list: List[ComplianceCheckResult] = Field(
        ...,
        description="Lista de empleados que no cumplen"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 2025,
                "total_employees": 100,
                "compliant_count": 85,
                "non_compliant_count": 15,
                "compliance_rate": 85.0,
                "non_compliant_list": []
            }
        }
    )


# ============================================
# EXPIRING SOON
# ============================================

class ExpiringSoonResult(BaseModel):
    """Empleado con dias por expirar."""
    employee_num: str = Field(..., description="Numero de empleado")
    name: Optional[str] = Field(None, description="Nombre")
    expiring_days: float = Field(..., description="Dias por expirar")
    expiry_date: str = Field(..., description="Fecha de expiracion")
    days_until_expiry: int = Field(..., description="Dias hasta expiracion")
    grant_year: int = Field(..., description="Ano de otorgamiento")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "name": "Taro Yamada",
                "expiring_days": 5,
                "expiry_date": "2025-03-20",
                "days_until_expiry": 60,
                "grant_year": 2023
            }
        }
    )


class ExpiringSoonSummary(BaseModel):
    """Resumen de vacaciones por expirar."""
    year: int = Field(..., description="Ano fiscal")
    threshold_months: int = Field(..., description="Umbral en meses")
    total_employees: int = Field(..., description="Empleados afectados")
    total_expiring_days: float = Field(..., description="Total dias por expirar")
    employees: List[ExpiringSoonResult] = Field(..., description="Detalle por empleado")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "year": 2025,
                "threshold_months": 3,
                "total_employees": 10,
                "total_expiring_days": 35.5,
                "employees": []
            }
        }
    )


# ============================================
# GRANT RECOMMENDATION
# ============================================

class GrantRecommendation(BaseModel):
    """Recomendacion de dias a otorgar."""
    employee_num: str = Field(..., description="Numero de empleado")
    hire_date: Optional[str] = Field(None, description="Fecha de contratacion")
    seniority_years: float = Field(..., description="Anos de antiguedad")
    recommended_days: int = Field(..., description="Dias recomendados")
    current_granted: float = Field(0, description="Dias actualmente otorgados")
    adjustment_needed: float = Field(0, description="Ajuste necesario")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "hire_date": "2022-04-01",
                "seniority_years": 2.5,
                "recommended_days": 12,
                "current_granted": 10,
                "adjustment_needed": 2
            }
        }
    )


# Export all
__all__ = [
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
]
