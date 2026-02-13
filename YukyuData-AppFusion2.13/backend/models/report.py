"""
Report Models - Schemas de reportes
Modelos Pydantic para generacion de reportes PDF y Excel
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============================================
# REPORT REQUEST MODELS
# ============================================

class CustomReportRequest(BaseModel):
    """Request para generar reporte personalizado."""
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Titulo del reporte"
    )
    year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Ano fiscal"
    )
    month: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Mes especifico (opcional)"
    )
    employee_nums: Optional[List[str]] = Field(
        None,
        description="Filtrar por empleados especificos"
    )
    haken_filter: Optional[str] = Field(
        None,
        description="Filtrar por lugar de trabajo"
    )
    include_charts: bool = Field(
        True,
        description="Incluir graficos"
    )
    include_compliance: bool = Field(
        True,
        description="Incluir seccion de compliance"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Monthly Vacation Report",
                "year": 2025,
                "month": 1,
                "include_charts": True,
                "include_compliance": True
            }
        }
    )


class MonthlyReportRequest(BaseModel):
    """Request para reporte mensual."""
    year: int = Field(..., ge=2000, le=2100, description="Ano")
    month: int = Field(..., ge=1, le=12, description="Mes")
    haken: Optional[str] = Field(None, description="Filtro por lugar de trabajo")
    active_only: bool = Field(True, description="Solo empleados activos")


class AnnualReportRequest(BaseModel):
    """Request para reporte anual."""
    year: int = Field(..., ge=2000, le=2100, description="Ano fiscal")
    include_monthly_breakdown: bool = Field(
        True,
        description="Incluir desglose mensual"
    )
    include_compliance_summary: bool = Field(
        True,
        description="Incluir resumen de compliance"
    )


# ============================================
# REPORT RESPONSE MODELS
# ============================================

class ReportMetadata(BaseModel):
    """Metadatos de un reporte generado."""
    id: str = Field(..., description="ID unico del reporte")
    title: str = Field(..., description="Titulo")
    type: str = Field(..., description="Tipo: monthly, annual, custom")
    format: str = Field(..., description="Formato: pdf, excel")
    year: int = Field(..., description="Ano")
    month: Optional[int] = Field(None, description="Mes (si aplica)")
    file_path: str = Field(..., description="Ruta del archivo")
    file_size: int = Field(..., description="Tamano en bytes")
    created_at: datetime = Field(..., description="Fecha de creacion")
    created_by: Optional[str] = Field(None, description="Usuario que lo creo")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "rpt_20250117_001",
                "title": "Monthly Report January 2025",
                "type": "monthly",
                "format": "pdf",
                "year": 2025,
                "month": 1,
                "file_path": "/reports/monthly_2025_01.pdf",
                "file_size": 125000,
                "created_at": "2025-01-17T10:00:00"
            }
        }
    )


class ReportListResponse(BaseModel):
    """Respuesta con lista de reportes disponibles."""
    status: str = Field("success")
    count: int = Field(..., description="Total de reportes")
    reports: List[ReportMetadata] = Field(..., description="Lista de reportes")


class ReportGenerateResponse(BaseModel):
    """Respuesta de generacion de reporte."""
    status: str = Field("success")
    message: str = Field(..., description="Mensaje de confirmacion")
    report: ReportMetadata = Field(..., description="Metadatos del reporte")
    download_url: str = Field(..., description="URL de descarga")


# ============================================
# REPORT DATA MODELS
# ============================================

class ReportSummaryStats(BaseModel):
    """Estadisticas de resumen para reportes."""
    total_employees: int = Field(..., description="Total empleados")
    total_granted: float = Field(..., description="Total dias otorgados")
    total_used: float = Field(..., description="Total dias usados")
    total_balance: float = Field(..., description="Total balance")
    usage_rate: float = Field(..., description="Tasa de uso (%)")
    compliance_rate: float = Field(..., description="Tasa de compliance (%)")
    employees_below_5days: int = Field(..., description="Empleados con menos de 5 dias")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_employees": 100,
                "total_granted": 1500,
                "total_used": 750,
                "total_balance": 750,
                "usage_rate": 50.0,
                "compliance_rate": 85.0,
                "employees_below_5days": 15
            }
        }
    )


class MonthlyBreakdown(BaseModel):
    """Desglose mensual para reportes."""
    month: int = Field(..., ge=1, le=12)
    month_name: str = Field(..., description="Nombre del mes")
    days_used: float = Field(0, description="Dias usados")
    requests_count: int = Field(0, description="Numero de solicitudes")
    employees_on_leave: int = Field(0, description="Empleados con ausencia")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "month": 1,
                "month_name": "January",
                "days_used": 45.5,
                "requests_count": 20,
                "employees_on_leave": 15
            }
        }
    )


class DepartmentBreakdown(BaseModel):
    """Desglose por departamento/haken."""
    haken: str = Field(..., description="Lugar de trabajo")
    employee_count: int = Field(..., description="Numero de empleados")
    total_granted: float = Field(0, description="Dias otorgados")
    total_used: float = Field(0, description="Dias usados")
    usage_rate: float = Field(0, description="Tasa de uso (%)")
    compliance_rate: float = Field(0, description="Tasa de compliance (%)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "haken": "ABC Corporation",
                "employee_count": 25,
                "total_granted": 375,
                "total_used": 200,
                "usage_rate": 53.3,
                "compliance_rate": 88.0
            }
        }
    )


class CustomReportData(BaseModel):
    """Datos completos para reporte personalizado."""
    title: str = Field(..., description="Titulo del reporte")
    year: int = Field(..., description="Ano fiscal")
    month: Optional[int] = Field(None, description="Mes")
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha de generacion"
    )
    summary: ReportSummaryStats = Field(..., description="Estadisticas resumen")
    monthly_breakdown: Optional[List[MonthlyBreakdown]] = Field(
        None,
        description="Desglose mensual"
    )
    department_breakdown: Optional[List[DepartmentBreakdown]] = Field(
        None,
        description="Desglose por departamento"
    )
    employees: Optional[List[dict]] = Field(None, description="Detalle de empleados")


# ============================================
# GITHUB MODELS (included here for convenience)
# ============================================

class CreateIssueRequest(BaseModel):
    """Request para crear issue en GitHub."""
    title: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Titulo del issue"
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Contenido del issue"
    )
    labels: Optional[List[str]] = Field(
        None,
        description="Etiquetas"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Bug: Error in calculation",
                "body": "Description of the issue...",
                "labels": ["bug", "priority-high"]
            }
        }
    )


class CommentRequest(BaseModel):
    """Request para agregar comentario a issue."""
    body: str = Field(
        ...,
        min_length=1,
        description="Contenido del comentario"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "body": "This has been fixed in PR #123"
            }
        }
    )


# Export all
__all__ = [
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
