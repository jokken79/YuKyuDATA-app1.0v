"""
Reports Routes
Endpoints de generacion de reportes PDF y Excel
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime
from pathlib import Path
import re

from ..dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    database,
    logger,
    get_active_employee_nums,
)
from services.reports import (
    ReportGenerator,
    save_report,
    list_reports,
    cleanup_old_reports,
    REPORTS_DIR
)

# Import centralized Pydantic models
from models import CustomReportRequest

router = APIRouter(prefix="/reports", tags=["Reports"])


# ============================================
# REPORT ENDPOINTS
# ============================================

@router.get("/custom")
async def get_custom_report_data(
    year: int = Query(..., ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    haken: Optional[str] = Query(None, max_length=100),
    active_only: bool = True,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get data for custom report generation.
    Obtiene datos para generacion de reportes personalizados.
    """
    try:
        employees = database.get_employees(year=year)

        if active_only:
            active_nums = get_active_employee_nums()
            employees = [
                e for e in employees
                if str(e.get('employee_num', '')) in active_nums
            ]

        if haken:
            employees = [e for e in employees if e.get('haken') == haken]

        # Calculate statistics
        total_granted = sum(e.get('granted', 0) for e in employees)
        total_used = sum(e.get('used', 0) for e in employees)
        total_balance = sum(e.get('balance', 0) for e in employees)

        below_5days = sum(1 for e in employees if e.get('used', 0) < 5)

        return {
            "status": "success",
            "year": year,
            "month": month,
            "active_only": active_only,
            "haken_filter": haken,
            "data": employees,
            "summary": {
                "count": len(employees),
                "total_granted": round(total_granted, 1),
                "total_used": round(total_used, 1),
                "total_balance": round(total_balance, 1),
                "usage_rate": round(total_used / total_granted * 100, 1) if total_granted > 0 else 0,
                "below_5days": below_5days,
                "compliance_rate": round((len(employees) - below_5days) / len(employees) * 100, 1) if employees else 0
            }
        }
    except Exception as e:
        logger.error(f"Failed to get custom report data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/monthly/{year}/{month}")
async def get_monthly_report_data(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get monthly report data for the 21st-20th period.
    Obtiene datos del reporte mensual para el periodo 21-20.
    """
    try:
        # Get usage details for the month
        usage_details = database.get_yukyu_usage_details(year=year, month=month)

        # Get approved requests for the month
        approved_requests = database.get_leave_requests(status='APPROVED', year=year)
        monthly_requests = [
            r for r in approved_requests
            if r.get('start_date', '').startswith(f"{year}-{month:02d}")
        ]

        # Calculate totals
        total_days = sum(u.get('days_used', 0) for u in usage_details)
        unique_employees = len(set(u.get('employee_num') for u in usage_details))

        return {
            "status": "success",
            "year": year,
            "month": month,
            "period": f"{year}-{month:02d}-21 to {year}-{month+1:02d}-20",
            "usage_details": usage_details,
            "approved_requests": monthly_requests,
            "summary": {
                "total_days_used": round(total_days, 1),
                "unique_employees": unique_employees,
                "request_count": len(monthly_requests)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get monthly report data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/monthly-list/{year}")
async def get_monthly_reports_list(
    year: int = Query(..., ge=2000, le=2100),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of monthly reports available for a year.
    Obtiene lista de reportes mensuales disponibles para un ano.
    """
    try:
        monthly_data = []

        for month in range(1, 13):
            usage = database.get_yukyu_usage_details(year=year, month=month)
            requests = database.get_leave_requests(status='APPROVED', year=year)
            monthly_requests = [
                r for r in requests
                if r.get('start_date', '').startswith(f"{year}-{month:02d}")
            ]

            monthly_data.append({
                "month": month,
                "month_name": datetime(year, month, 1).strftime("%B"),
                "usage_count": len(usage),
                "total_days": sum(u.get('days_used', 0) for u in usage),
                "request_count": len(monthly_requests),
                "has_data": len(usage) > 0 or len(monthly_requests) > 0
            })

        return {
            "status": "success",
            "year": year,
            "months": monthly_data
        }
    except Exception as e:
        logger.error(f"Failed to get monthly reports list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# PDF REPORT ENDPOINTS
# ============================================

@router.get("/employee/{employee_num}/pdf")
async def get_employee_pdf_report(
    employee_num: str = Query(..., min_length=1, max_length=10),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Generate PDF report for an individual employee.
    Genera reporte PDF para un empleado individual.
    """
    try:
        if year is None:
            year = datetime.now().year

        generator = ReportGenerator()
        pdf_bytes = generator.generate_employee_report(employee_num, year)

        filename = f"employee_{employee_num}_{year}.pdf"
        filepath = save_report(pdf_bytes, filename)

        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error generating employee PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/annual/{year}/pdf")
async def get_annual_pdf_report(
    year: int = Query(..., ge=2000, le=2100),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Generate annual PDF report.
    Genera reporte PDF anual.
    """
    try:
        generator = ReportGenerator()
        pdf_bytes = generator.generate_annual_report(year)

        filename = f"annual_report_{year}.pdf"
        filepath = save_report(pdf_bytes, filename)

        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error generating annual PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/monthly/{year}/{month}/pdf")
async def get_monthly_pdf_report(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Generate monthly PDF report.
    Genera reporte PDF mensual.
    """
    try:
        generator = ReportGenerator()
        pdf_bytes = generator.generate_monthly_report(year, month)

        filename = f"monthly_report_{year}_{month:02d}.pdf"
        filepath = save_report(pdf_bytes, filename)

        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error generating monthly PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/compliance/{year}/pdf")
async def get_compliance_pdf_report(
    year: int = Query(..., ge=2000, le=2100),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Generate compliance PDF report.
    Genera reporte PDF de cumplimiento.
    """
    try:
        generator = ReportGenerator()
        pdf_bytes = generator.generate_compliance_report(year)

        filename = f"compliance_report_{year}.pdf"
        filepath = save_report(pdf_bytes, filename)

        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error generating compliance PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/custom/pdf")
async def generate_custom_pdf_report(
    report_request: CustomReportRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Generate custom PDF report with specified parameters.
    Genera reporte PDF personalizado con parametros especificados.
    """
    try:
        generator = ReportGenerator()
        pdf_bytes = generator.generate_custom_report(
            title=report_request.title,
            year=report_request.year,
            month=report_request.month,
            employee_nums=report_request.employee_nums,
            haken_filter=report_request.haken_filter,
            include_charts=report_request.include_charts,
            include_compliance=report_request.include_compliance
        )

        safe_title = re.sub(r'[^\w\-_]', '_', report_request.title)[:50]
        filename = f"custom_{safe_title}_{report_request.year}.pdf"
        filepath = save_report(pdf_bytes, filename)

        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error generating custom PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# REPORT FILE MANAGEMENT
# ============================================

@router.get("/files")
async def list_report_files(user: CurrentUser = Depends(get_current_user)):
    """
    List available report files.
    Lista archivos de reportes disponibles.
    """
    try:
        reports = list_reports()
        return {
            "status": "success",
            "count": len(reports),
            "reports": reports
        }
    except Exception as e:
        logger.error(f"Failed to list report files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download/{filename}")
async def download_report(filename: str, user: CurrentUser = Depends(get_current_user)):
    """
    Download a specific report file.
    Descarga un archivo de reporte especifico.
    """
    try:
        safe_filename = Path(filename).name
        filepath = REPORTS_DIR / safe_filename

        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        if not filepath.suffix.lower() in ['.pdf', '.xlsx', '.csv']:
            raise HTTPException(status_code=400, detail="Invalid file type")

        media_type = {
            '.pdf': 'application/pdf',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv'
        }.get(filepath.suffix.lower(), 'application/octet-stream')

        return FileResponse(
            path=str(filepath),
            media_type=media_type,
            filename=safe_filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/cleanup")
async def cleanup_pdf_reports(
    days_to_keep: int = 30,
    user: CurrentUser = Depends(get_admin_user)
):
    """
    Delete old PDF reports (requires admin authentication).
    Elimina reportes PDF antiguos (requiere autenticacion admin).
    """
    try:
        deleted = cleanup_old_reports(days_to_keep)
        logger.info(f"PDF cleanup by {user.username}: {deleted} files deleted")
        return {
            "status": "success",
            "deleted_count": deleted,
            "days_threshold": days_to_keep
        }
    except Exception as e:
        logger.error(f"Error cleaning up reports: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
