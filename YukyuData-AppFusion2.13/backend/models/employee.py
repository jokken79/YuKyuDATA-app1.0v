"""
Employee Models - Schemas de empleados
Modelos Pydantic para gestion de empleados y datos de vacaciones
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class EmployeeStatus(str, Enum):
    """Estado del empleado."""
    ACTIVE = "在職中"
    RESIGNED = "退職"


class EmployeeType(str, Enum):
    """Tipo de empleado."""
    GENZAI = "genzai"    # Despacho (派遣社員)
    UKEOI = "ukeoi"      # Contratista (請負社員)
    STAFF = "staff"      # Oficina


# ============================================
# BASE MODELS
# ============================================

class EmployeeBase(BaseModel):
    """Campos base compartidos por empleados."""
    employee_num: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Numero de empleado"
    )
    name: Optional[str] = Field(None, description="Nombre del empleado")
    haken: Optional[str] = Field(None, description="Lugar de trabajo (派遣先)")

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class EmployeeCreate(EmployeeBase):
    """Modelo para crear un nuevo empleado."""
    year: int = Field(..., ge=2000, le=2100, description="Ano fiscal")
    granted: float = Field(0, ge=0, le=40, description="Dias otorgados")
    used: float = Field(0, ge=0, le=40, description="Dias usados")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_num": "001",
                "name": "Taro Yamada",
                "haken": "ABC Corporation",
                "year": 2025,
                "granted": 10,
                "used": 0
            }
        }
    )


class EmployeeUpdate(BaseModel):
    """Modelo para actualizar datos de empleado."""
    name: Optional[str] = Field(None, description="Nombre del empleado")
    haken: Optional[str] = Field(None, description="Lugar de trabajo")
    granted: Optional[float] = Field(
        None,
        ge=0,
        le=40,
        description="Dias otorgados (0-40)"
    )
    used: Optional[float] = Field(
        None,
        ge=0,
        le=40,
        description="Dias usados (0-40)"
    )
    validate_limit: bool = Field(
        True,
        description="Validar limite de 40 dias acumulados"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Taro Yamada",
                "granted": 15,
                "validate_limit": True
            }
        }
    )


class EmployeeResponse(BaseModel):
    """Modelo de respuesta para datos de empleado."""
    id: str = Field(..., description="ID compuesto (employee_num_year)")
    employee_num: str = Field(..., description="Numero de empleado")
    name: Optional[str] = Field(None, description="Nombre")
    kana: Optional[str] = Field(None, description="Nombre en Katakana")
    haken: Optional[str] = Field(None, description="Lugar de trabajo")
    granted: float = Field(0, description="Dias otorgados")
    used: float = Field(0, description="Dias usados")
    balance: float = Field(0, description="Saldo disponible")
    expired: float = Field(0, description="Dias expirados")
    usage_rate: float = Field(0, description="Tasa de uso (%)")
    year: int = Field(..., description="Ano fiscal")
    created_at: Optional[datetime] = Field(None, description="Fecha de creacion")
    updated_at: Optional[datetime] = Field(None, description="Fecha de actualizacion")

    # Campos adicionales para respuesta enriquecida
    employee_type: Optional[str] = Field(None, description="Tipo de empleado")
    employment_status: Optional[str] = Field(None, description="Estado de empleo")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "001_2025",
                "employee_num": "001",
                "name": "Taro Yamada",
                "haken": "ABC Corporation",
                "granted": 10,
                "used": 3,
                "balance": 7,
                "expired": 0,
                "usage_rate": 30.0,
                "year": 2025
            }
        }
    )


# ============================================
# BULK UPDATE MODELS
# ============================================

class BulkUpdateRequest(BaseModel):
    """Modelo para actualizar multiples empleados en una operacion."""
    employee_nums: List[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Lista de numeros de empleado (max 50)"
    )
    year: int = Field(..., ge=2000, le=2100, description="Ano fiscal")
    updates: dict = Field(..., description="Campos a actualizar")
    validate_limit: bool = Field(
        True,
        description="Validar limite de 40 dias acumulados"
    )

    @field_validator('employee_nums')
    @classmethod
    def validate_employee_nums(cls, v):
        if len(v) > 50:
            raise ValueError('Maximo 50 empleados por operacion')
        if len(v) == 0:
            raise ValueError('Se requiere al menos un empleado')
        return v

    @field_validator('updates')
    @classmethod
    def validate_updates(cls, v):
        if not v:
            raise ValueError('Se requiere al menos un campo a actualizar')
        valid_fields = {'add_granted', 'add_used', 'set_haken', 'set_granted', 'set_used'}
        invalid = set(v.keys()) - valid_fields
        if invalid:
            raise ValueError(f'Campos invalidos: {invalid}. Validos: {valid_fields}')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_nums": ["001", "002", "003"],
                "year": 2025,
                "updates": {"add_granted": 5},
                "validate_limit": True
            }
        }
    )


class BulkUpdatePreview(BaseModel):
    """Modelo para previsualizar cambios de bulk update."""
    employee_nums: List[str] = Field(..., min_length=1, max_length=50)
    year: int = Field(..., ge=2000, le=2100)
    updates: dict

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_nums": ["001", "002"],
                "year": 2025,
                "updates": {"set_granted": 20}
            }
        }
    )


class BulkUpdateResult(BaseModel):
    """Resultado de operacion de actualizacion masiva."""
    success: bool = Field(..., description="Si la operacion fue exitosa")
    updated_count: int = Field(..., description="Numero de registros actualizados")
    failed_count: int = Field(0, description="Numero de registros fallidos")
    errors: Optional[List[str]] = Field(None, description="Lista de errores")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "updated_count": 3,
                "failed_count": 0,
                "errors": None
            }
        }
    )


# ============================================
# EMPLOYEE LIST MODELS
# ============================================

class EmployeeListResponse(BaseModel):
    """Respuesta para lista de empleados."""
    status: str = Field("success")
    data: List[EmployeeResponse] = Field(..., description="Lista de empleados")
    years: List[int] = Field(..., description="Anos disponibles")
    count: Optional[int] = Field(None, description="Total de empleados")


class EmployeeSearchRequest(BaseModel):
    """Modelo para busqueda de empleados."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Termino de busqueda"
    )
    year: Optional[int] = Field(None, ge=2000, le=2100, description="Filtrar por ano")
    haken: Optional[str] = Field(None, description="Filtrar por lugar de trabajo")
    status: Optional[EmployeeStatus] = Field(None, description="Filtrar por estado")
    limit: int = Field(50, ge=1, le=200, description="Maximo resultados")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "Yamada",
                "year": 2025,
                "limit": 50
            }
        }
    )


# Export all
__all__ = [
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
]
