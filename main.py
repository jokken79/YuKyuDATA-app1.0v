from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import shutil
import os
from pathlib import Path
from datetime import datetime

# Local modules
import database
import excel_service

app = FastAPI(title="YuKyu Dashboard API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
DEFAULT_EXCEL_PATH = r"D:\YuKyuDATA-app\有給休暇管理.xlsm"
EMPLOYEE_REGISTRY_PATH = r"D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize Database
database.init_db()

# Mount static files (css, js, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serves the main dashboard page."""
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/employees")
async def get_employees(year: int = None):
    """Returns list of employees from SQLite."""
    try:
        data = database.get_employees(year)
        years = database.get_available_years()
        return {"data": data, "available_years": years}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync")
async def sync_default_file():
    """Triggers auto-read of the default Excel file + individual usage dates."""
    if not os.path.exists(DEFAULT_EXCEL_PATH):
        raise HTTPException(status_code=404, detail=f"Default file not found at {DEFAULT_EXCEL_PATH}")

    try:
        # Parse summary data (totals)
        data = excel_service.parse_excel_file(DEFAULT_EXCEL_PATH)
        database.save_employees(data)

        # Parse individual usage dates (columns R-BE - v2.0 feature)
        usage_details = excel_service.parse_yukyu_usage_details(DEFAULT_EXCEL_PATH)
        database.save_yukyu_usage_details(usage_details)

        return {
            "status": "success",
            "count": len(data),
            "usage_details_count": len(usage_details),
            "message": f"Synced {len(data)} employees + {len(usage_details)} individual usage dates"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handles manual Excel file upload and processing."""
    try:
        # Save temp file
        temp_path = UPLOAD_DIR / file.filename
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process
        data = excel_service.parse_excel_file(str(temp_path))
        database.save_employees(data)
        
        # Cleanup
        os.remove(temp_path)
        
        return {"status": "success", "count": len(data), "message": f"Successfully imported {len(data)} records"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.delete("/api/reset")
async def reset_db():
    database.clear_database()
    return {"status": "success", "message": "Database cleared"}

# === GENZAI (Dispatch Employees) Endpoints ===

@app.get("/api/genzai")
async def get_genzai(status: str = None):
    """Returns list of dispatch employees from DBGenzaiX. Optional status filter."""
    try:
        data = database.get_genzai(status)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync-genzai")
async def sync_genzai():
    """Syncs DBGenzaiX sheet from employee registry file."""
    if not os.path.exists(EMPLOYEE_REGISTRY_PATH):
        raise HTTPException(status_code=404, detail=f"Employee registry file not found at {EMPLOYEE_REGISTRY_PATH}")

    try:
        data = excel_service.parse_genzai_sheet(EMPLOYEE_REGISTRY_PATH)
        database.save_genzai(data)
        return {"status": "success", "count": len(data), "message": f"Genzai synced: {len(data)} dispatch employees"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Genzai sync failed: {str(e)}")

@app.delete("/api/reset-genzai")
async def reset_genzai():
    """Clears genzai table."""
    database.clear_genzai()
    return {"status": "success", "message": "Genzai database cleared"}

# === UKEOI (Contract Employees) Endpoints ===

@app.get("/api/ukeoi")
async def get_ukeoi(status: str = None):
    """Returns list of contract employees from DBUkeoiX. Optional status filter."""
    try:
        data = database.get_ukeoi(status)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync-ukeoi")
async def sync_ukeoi():
    """Syncs DBUkeoiX sheet from employee registry file."""
    if not os.path.exists(EMPLOYEE_REGISTRY_PATH):
        raise HTTPException(status_code=404, detail=f"Employee registry file not found at {EMPLOYEE_REGISTRY_PATH}")

    try:
        data = excel_service.parse_ukeoi_sheet(EMPLOYEE_REGISTRY_PATH)
        database.save_ukeoi(data)
        return {"status": "success", "count": len(data), "message": f"Ukeoi synced: {len(data)} contract employees"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ukeoi sync failed: {str(e)}")

@app.delete("/api/reset-ukeoi")
async def reset_ukeoi():
    """Clears ukeoi table."""
    database.clear_ukeoi()
    return {"status": "success", "message": "Ukeoi database cleared"}

# === STATISTICS Endpoints ===

@app.get("/api/stats/by-factory")
async def get_factory_stats(year: int = None):
    """Returns vacation usage statistics grouped by factory (派遣先). Optional year filter."""
    try:
        data = database.get_stats_by_factory(year)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === LEAVE REQUEST ENDPOINTS ===

@app.get("/api/employees/search")
async def search_employees(q: str = "", status: str = None):
    """Search for employees in genzai and ukeoi tables. Optional status filter (在職中)."""
    try:
        results = []

        # Search in genzai (dispatch employees)
        genzai = database.get_genzai(status)
        for emp in genzai:
            if q.lower() in emp.get('name', '').lower() or \
               q.lower() in emp.get('employee_num', '').lower() or \
               q.lower() in emp.get('dispatch_name', '').lower():
                results.append({
                    "employee_num": emp.get('employee_num'),
                    "name": emp.get('name'),
                    "factory": emp.get('dispatch_name'),
                    "status": emp.get('status'),
                    "type": "派遣"
                })

        # Search in ukeoi (contract employees)
        ukeoi = database.get_ukeoi(status)
        for emp in ukeoi:
            if q.lower() in emp.get('name', '').lower() or \
               q.lower() in emp.get('employee_num', '').lower() or \
               q.lower() in emp.get('contract_business', '').lower():
                results.append({
                    "employee_num": emp.get('employee_num'),
                    "name": emp.get('name'),
                    "factory": emp.get('contract_business'),
                    "status": emp.get('status'),
                    "type": "請負"
                })

        return {"status": "success", "data": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employees/{employee_num}/leave-info")
async def get_employee_leave_info(employee_num: str):
    """Get complete leave information for an employee (current + previous year)."""
    try:
        from datetime import datetime
        current_year = datetime.now().year

        # Get employee data from genzai or ukeoi
        employee_data = None
        genzai_list = database.get_genzai()
        for emp in genzai_list:
            if emp.get('employee_num') == employee_num:
                employee_data = {
                    "employee_num": emp.get('employee_num'),
                    "name": emp.get('name'),
                    "factory": emp.get('dispatch_name'),
                    "status": emp.get('status'),
                    "type": "派遣"
                }
                break

        if not employee_data:
            ukeoi_list = database.get_ukeoi()
            for emp in ukeoi_list:
                if emp.get('employee_num') == employee_num:
                    employee_data = {
                        "employee_num": emp.get('employee_num'),
                        "name": emp.get('name'),
                        "factory": emp.get('contract_business'),
                        "status": emp.get('status'),
                        "type": "請負"
                    }
                    break

        if not employee_data:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Get yukyu history (current + previous year)
        history = database.get_employee_yukyu_history(employee_num, current_year)

        # Get pending requests
        pending_requests = database.get_leave_requests(status='PENDING', employee_num=employee_num)

        # Calculate total available (sum of balances from history)
        total_available = sum(record.get('balance', 0) for record in history)

        return {
            "status": "success",
            "employee": employee_data,
            "yukyu_history": history,
            "total_available": round(total_available, 1),
            "pending_requests": pending_requests
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/leave-requests")
async def create_leave_request(request_data: dict):
    """Create a new leave request."""
    try:
        from datetime import datetime

        # Validate required fields
        required = ['employee_num', 'employee_name', 'start_date', 'end_date', 'days_requested']
        for field in required:
            if field not in request_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Get current year
        current_year = datetime.now().year

        # Validate employee has sufficient balance
        history = database.get_employee_yukyu_history(request_data['employee_num'], current_year)
        total_available = sum(record.get('balance', 0) for record in history)

        if request_data['days_requested'] > total_available:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Available: {total_available} days, Requested: {request_data['days_requested']} days"
            )

        # Create request
        request_id = database.create_leave_request(
            employee_num=request_data['employee_num'],
            employee_name=request_data['employee_name'],
            start_date=request_data['start_date'],
            end_date=request_data['end_date'],
            days_requested=request_data['days_requested'],
            reason=request_data.get('reason', ''),
            year=current_year
        )

        return {
            "status": "success",
            "message": "Leave request created successfully",
            "request_id": request_id
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leave-requests")
async def get_leave_requests_list(status: str = None, employee_num: str = None, year: int = None):
    """Get list of leave requests with optional filters."""
    try:
        requests = database.get_leave_requests(status=status, employee_num=employee_num, year=year)
        return {"status": "success", "data": requests, "count": len(requests)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/leave-requests/{request_id}/approve")
async def approve_leave_request(request_id: int, approval_data: dict):
    """Approve a leave request and automatically update yukyu balance."""
    try:
        approved_by = approval_data.get('approved_by', 'Manager')

        # Approve request (this also updates the yukyu balance automatically)
        database.approve_leave_request(request_id, approved_by)

        return {
            "status": "success",
            "message": "Request approved and yukyu balance updated"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/leave-requests/{request_id}/reject")
async def reject_leave_request(request_id: int, rejection_data: dict):
    """Reject a leave request."""
    try:
        rejected_by = rejection_data.get('rejected_by', 'Manager')

        database.reject_leave_request(request_id, rejected_by)

        return {
            "status": "success",
            "message": "Request rejected"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === YUKYU USAGE DETAILS ENDPOINTS (v2.0 Features) ===

@app.get("/api/yukyu/usage-details")
async def get_usage_details(employee_num: str = None, year: int = None, month: int = None):
    """Get individual yukyu usage dates (v2.0 feature: 使用日一覧)."""
    try:
        details = database.get_yukyu_usage_details(employee_num, year, month)
        return {"status": "success", "data": details, "count": len(details)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/yukyu/monthly-summary/{year}")
async def get_monthly_summary(year: int):
    """Get monthly usage summary for a year (v2.0 feature: 月別フィルター)."""
    try:
        summary = database.get_monthly_usage_summary(year)

        # Also get employee list for each month
        monthly_data = []
        for month in range(1, 13):
            month_details = database.get_yukyu_usage_details(year=year, month=month)

            # Get unique employees for this month
            employees_in_month = {}
            for detail in month_details:
                emp_num = detail['employee_num']
                if emp_num not in employees_in_month:
                    employees_in_month[emp_num] = {
                        'employee_num': emp_num,
                        'name': detail['name'],
                        'days_used': 0,
                        'dates': []
                    }
                employees_in_month[emp_num]['days_used'] += detail['days_used']
                employees_in_month[emp_num]['dates'].append(detail['use_date'])

            monthly_data.append({
                'month': month,
                'employee_count': len(employees_in_month),
                'total_days': summary.get(month, {}).get('total_days', 0),
                'employees': list(employees_in_month.values())
            })

        return {"status": "success", "year": year, "data": monthly_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/yukyu/by-employee-type/{year}")
async def get_usage_by_employee_type(year: int):
    """Get yukyu usage breakdown by employee type (派遣/請負/スタッフ) for a year."""
    try:
        # Get all yukyu data for the year
        yukyu_data = database.get_employees(year=year)

        # Get employee lists
        genzai_employees = database.get_genzai()
        ukeoi_employees = database.get_ukeoi()

        # Create sets for quick lookup
        genzai_nums = {emp['employee_num'] for emp in genzai_employees if emp.get('employee_num')}
        ukeoi_nums = {emp['employee_num'] for emp in ukeoi_employees if emp.get('employee_num')}

        # Classify and aggregate
        hakenshain = {'employees': [], 'total_used': 0, 'count': 0}
        ukeoi = {'employees': [], 'total_used': 0, 'count': 0}
        staff = {'employees': [], 'total_used': 0, 'count': 0}

        for emp in yukyu_data:
            emp_num = str(emp['employee_num']) if emp['employee_num'] else None

            if emp_num in genzai_nums:
                hakenshain['employees'].append(emp)
                hakenshain['total_used'] += emp['used']
                hakenshain['count'] += 1
            elif emp_num in ukeoi_nums:
                ukeoi['employees'].append(emp)
                ukeoi['total_used'] += emp['used']
                ukeoi['count'] += 1
            elif emp_num:
                staff['employees'].append(emp)
                staff['total_used'] += emp['used']
                staff['count'] += 1

        total_used = hakenshain['total_used'] + ukeoi['total_used'] + staff['total_used']

        return {
            "status": "success",
            "year": year,
            "total_used": total_used,
            "breakdown": {
                "hakenshain": {
                    "count": hakenshain['count'],
                    "total_used": hakenshain['total_used'],
                    "percentage": round((hakenshain['total_used'] / total_used * 100), 1) if total_used > 0 else 0
                },
                "ukeoi": {
                    "count": ukeoi['count'],
                    "total_used": ukeoi['total_used'],
                    "percentage": round((ukeoi['total_used'] / total_used * 100), 1) if total_used > 0 else 0
                },
                "staff": {
                    "count": staff['count'],
                    "total_used": staff['total_used'],
                    "percentage": round((staff['total_used'] / total_used * 100), 1) if total_used > 0 else 0
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === COMPLIANCE & AGENT ENDPOINTS ===

@app.get("/api/compliance/5day-check/{year}")
async def check_5day_compliance(year: int):
    """
    Verifica cumplimiento de 5日取得義務 para todos los empleados.
    Retorna empleados que no cumplen con el mínimo de 5 días.
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

@app.get("/api/compliance/expiring/{year}")
async def check_expiring_balances(year: int, warning_days: int = 30):
    """
    Verifica balances próximos a expirar.
    Retorna empleados con días que expiran dentro del período de alerta.
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

@app.get("/api/compliance/report/{year}")
async def get_compliance_report(year: int):
    """
    Genera un reporte completo de compliance para el año especificado.
    Incluye: 5日取得義務, expiración, alertas.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()
        report = compliance.get_compliance_report(year)
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compliance/alerts")
async def get_compliance_alerts():
    """
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

@app.get("/api/compliance/annual-ledger/{year}")
async def get_annual_ledger(year: int):
    """
    Genera el 年次有給休暇管理簿 (libro de gestión de vacaciones anuales).
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

@app.post("/api/compliance/export-ledger/{year}")
async def export_annual_ledger(year: int, format: str = "csv"):
    """
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
                "message": f"年次有給休暇管理簿 exported successfully",
                "filename": filename,
                "path": str(output_path)
            }
        else:
            raise HTTPException(status_code=500, detail="Export failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === SYSTEM STATUS & AUDIT ENDPOINTS ===

@app.get("/api/system/snapshot")
async def get_system_snapshot():
    """
    Obtiene un snapshot del estado actual del sistema.
    Útil para monitoreo y debugging.
    """
    try:
        from agents.documentor import get_documentor
        documentor = get_documentor()
        snapshot = documentor.get_system_snapshot()
        return {"status": "success", "snapshot": snapshot.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/audit-log")
async def get_audit_log(
    action: str = None,
    entity_type: str = None,
    limit: int = 100
):
    """
    Obtiene el historial de auditoría del sistema.
    Filtrable por tipo de acción y entidad.
    """
    try:
        from agents.documentor import get_documentor
        documentor = get_documentor()
        entries = documentor.search_history(
            action=action,
            entity_type=entity_type,
            limit=limit
        )
        return {"status": "success", "count": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/activity-report")
async def get_activity_report(days: int = 7):
    """
    Genera un reporte de actividad para los últimos N días.
    """
    try:
        from agents.documentor import get_documentor
        from datetime import timedelta
        documentor = get_documentor()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        report = documentor.generate_activity_report(
            start_date.isoformat(),
            end_date.isoformat()
        )
        return {"status": "success", "report": report.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === NOTIFICATIONS ENDPOINTS ===

@app.get("/api/notifications")
async def get_notifications(employee_num: str = None, unread_only: bool = False):
    """
    Obtiene notificaciones del sistema.
    Las notificaciones incluyen alertas de compliance, solicitudes aprobadas/rechazadas, etc.
    """
    try:
        from agents.compliance import get_compliance
        compliance = get_compliance()

        # Obtener alertas como notificaciones
        alerts = compliance.get_active_alerts()

        notifications = []
        for alert in alerts:
            if employee_num and alert.employee_num != employee_num:
                continue

            notifications.append({
                "id": alert.alert_id,
                "type": alert.type,
                "level": alert.level.value,
                "title": alert.type.replace('_', ' ').title(),
                "message": alert.message_ja,
                "employee_num": alert.employee_num,
                "created_at": alert.created_at,
                "is_read": False  # Por implementar
            })

        return {
            "status": "success",
            "count": len(notifications),
            "notifications": notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

