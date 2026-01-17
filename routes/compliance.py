"""
Compliance Routes
Endpoints de cumplimiento normativo (5日取得義務, etc.)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from .dependencies import (
    get_current_user,
    CurrentUser,
    database,
    logger,
    UPLOAD_DIR,
)

router = APIRouter(prefix="/api/compliance", tags=["Compliance"])


# ============================================
# COMPLIANCE ENDPOINTS
# ============================================

@router.get("/5day-check/{year}")
async def check_5day_compliance_endpoint(year: int):
    """
    Check 5-day usage obligation compliance for all employees.
    Verifica cumplimiento de 5日取得義務 para todos los empleados.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()
        results = compliance.check_all_5_day_compliance(year)

        return {
            "status": "success",
            "year": year,
            "summary": {
                "total_checked": results['total_checked'],
                "compliant": results['compliant'],
                "at_risk": results['at_risk'],
                "non_compliant": results['non_compliant'],
                "compliance_rate": results.get('compliance_rate', 0)
            },
            "non_compliant_employees": [
                {
                    "employee_num": c.employee_num,
                    "name": c.employee_name,
                    "days_used": c.days_used,
                    "days_remaining": c.days_remaining,
                    "status": c.status.value
                }
                for c in results['checks']
                if c.status.value != 'compliant'
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring/{year}")
async def check_expiring_balances(year: int, warning_days: int = 30):
    """
    Check balances close to expiring.
    Verifica balances proximos a expirar.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()
        results = compliance.check_expiring_balances(year, warning_days)

        return {
            "status": "success",
            "year": year,
            "warning_days": warning_days,
            "count": len(results),
            "employees": [
                {
                    "employee_num": r.employee_num,
                    "name": r.employee_name,
                    "expiring_days": r.expiring_days,
                    "expiry_date": r.expiry_date,
                    "days_until_expiry": r.days_until_expiry,
                    "alert_level": r.alert_level.value
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{year}")
async def get_compliance_report(year: int):
    """
    Generate a complete compliance report for the specified year.
    Genera un reporte completo de compliance para el ano especificado.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()
        report = compliance.get_compliance_report(year)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_compliance_alerts():
    """
    Get all active compliance alerts.
    Obtiene todas las alertas de compliance activas.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()
        alerts = compliance.get_active_alerts()
        summary = compliance.get_alerts_summary()

        return {
            "status": "success",
            "summary": summary,
            "alerts": [
                {
                    "id": a.alert_id,
                    "level": a.level.value,
                    "type": a.type,
                    "employee_num": a.employee_num,
                    "employee_name": a.employee_name,
                    "message": a.message,
                    "message_ja": a.message_ja,
                    "action_required": a.action_required,
                    "created_at": a.created_at
                }
                for a in alerts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annual-ledger/{year}")
async def get_annual_ledger(year: int):
    """
    Generate the 年次有給休暇管理簿 (Annual Paid Leave Ledger).
    Document required by law since 2019.

    Genera el 年次有給休暇管理簿 (libro de gestion de vacaciones anuales).
    Documento requerido por ley desde 2019.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()
        entries = compliance.generate_annual_ledger(year)

        return {
            "status": "success",
            "year": year,
            "document_name": "年次有給休暇管理簿",
            "count": len(entries),
            "entries": [
                {
                    "employee_num": e.employee_num,
                    "employee_name": e.employee_name,
                    "grant_date": e.grant_date,
                    "granted_days": e.granted_days,
                    "used_dates": e.used_dates,
                    "used_days": e.used_days,
                    "remaining_days": e.remaining_days
                }
                for e in entries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-ledger/{year}")
async def export_annual_ledger(year: int, format: str = "csv"):
    """
    Export the 年次有給休暇管理簿 to file.
    Formats: csv, json

    Exporta el 年次有給休暇管理簿 a archivo.
    Formatos: csv, json
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()

        filename = f"年次有給休暇管理簿_{year}.{format}"
        output_path = UPLOAD_DIR / filename

        success = compliance.export_annual_ledger(year, str(output_path), format)

        if success:
            return {
                "status": "success",
                "message": "年次有給休暇管理簿 exported successfully",
                "filename": filename,
                "path": str(output_path)
            }
        else:
            raise HTTPException(status_code=500, detail="Export failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
