"""
Common Models - Schemas comunes reutilizables
Modelos base y respuestas estandarizadas para la API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional, Dict, List, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


# ============================================
# BASE RESPONSE MODELS
# ============================================

class APIResponse(BaseModel):
    """
    Modelo estandarizado de respuesta API.

    Attributes:
        success: Indica si la operacion fue exitosa
        status: String "success" o "error" (para compatibilidad con frontend)
        data: Datos de la respuesta (puede ser dict, list, etc.)
        message: Mensaje descriptivo opcional
        error: Descripcion del error (solo cuando success=False)
        count: Numero de items (opcional, para listas)
    """
    success: bool = Field(..., description="Indica si la operacion fue exitosa")
    status: str = Field(..., description="'success' o 'error' para compatibilidad")
    data: Optional[Any] = Field(None, description="Datos de la respuesta")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")
    error: Optional[str] = Field(None, description="Descripcion del error")
    count: Optional[int] = Field(None, description="Numero de items en data (si es lista)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "status": "success",
                    "data": {"id": 1, "name": "Test"},
                    "message": "Operation completed successfully"
                },
                {
                    "success": False,
                    "status": "error",
                    "error": "ValidationError",
                    "message": "Invalid input data"
                }
            ]
        }
    )


class ErrorResponse(BaseModel):
    """
    Modelo estandarizado de respuesta de error.
    """
    success: bool = Field(False, description="Siempre False para errores")
    status: str = Field("error", description="Siempre 'error'")
    error: str = Field(..., description="Codigo o tipo de error")
    message: Optional[str] = Field(None, description="Mensaje descriptivo del error")
    field_errors: Optional[Dict[str, str]] = Field(
        None,
        description="Errores por campo (para validacion)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "status": "error",
                "error": "ValidationError",
                "message": "Invalid input data",
                "field_errors": {"year": "Must be between 2000 and 2100"}
            }
        }
    )


class PaginatedResponse(APIResponse):
    """
    Modelo de respuesta paginada.
    Extiende APIResponse con informacion de paginacion.
    """
    pagination: Optional[Dict[str, int]] = Field(
        None,
        description="Informacion de paginacion",
        json_schema_extra={
            "example": {
                "page": 1,
                "limit": 50,
                "total": 150,
                "total_pages": 3
            }
        }
    )


class PaginationInfo(BaseModel):
    """Informacion de paginacion detallada."""
    page: int = Field(..., ge=1, description="Numero de pagina actual (1-indexed)")
    limit: int = Field(..., ge=1, le=500, description="Items por pagina")
    total: int = Field(..., ge=0, description="Total de items")
    total_pages: int = Field(..., ge=0, description="Total de paginas")
    has_next: bool = Field(..., description="Si existe pagina siguiente")
    has_prev: bool = Field(..., description="Si existe pagina anterior")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "limit": 50,
                "total": 150,
                "total_pages": 3,
                "has_next": True,
                "has_prev": False
            }
        }
    )


# ============================================
# PAGINATION PARAMS
# ============================================

class PaginationParams(BaseModel):
    """Parametros de paginacion para queries."""
    page: int = Field(1, ge=1, description="Numero de pagina (1-indexed)")
    per_page: int = Field(20, ge=1, le=100, description="Items por pagina (max 100)")
    sort_by: Optional[str] = Field(None, description="Columna para ordenar")
    sort_order: Optional[str] = Field(
        "asc",
        pattern="^(asc|desc)$",
        description="Direccion del orden"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "per_page": 20,
                "sort_by": "name",
                "sort_order": "asc"
            }
        }
    )


# ============================================
# DATE RANGE QUERY
# ============================================

class DateRangeQuery(BaseModel):
    """Modelo para consultas por rango de fechas."""
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            }
        }
    )


# ============================================
# STATUS RESPONSE
# ============================================

class StatusResponse(BaseModel):
    """Respuesta de estado del sistema."""
    status: str = Field(..., description="Estado: 'ok', 'warning', 'error'")
    version: Optional[str] = Field(None, description="Version de la aplicacion")
    uptime: Optional[float] = Field(None, description="Tiempo de actividad en segundos")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de la respuesta"
    )
    checks: Optional[Dict[str, Any]] = Field(
        None,
        description="Resultados de health checks"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "version": "5.16",
                "uptime": 86400.5,
                "timestamp": "2025-01-17T10:00:00",
                "checks": {
                    "database": "healthy",
                    "disk": "healthy"
                }
            }
        }
    )


# ============================================
# YEAR FILTER
# ============================================

class YearFilter(BaseModel):
    """Filtro por ano fiscal."""
    year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Ano fiscal (2000-2100)"
    )


# Export all
__all__ = [
    'APIResponse',
    'ErrorResponse',
    'PaginatedResponse',
    'PaginationInfo',
    'PaginationParams',
    'DateRangeQuery',
    'StatusResponse',
    'YearFilter',
]
