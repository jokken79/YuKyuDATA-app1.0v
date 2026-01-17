"""
Yukyu (Vacation) Details Routes
Endpoints de detalles de uso de vacaciones
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

from .dependencies import (
    get_current_user,
    CurrentUser,
    database,
    logger,
    log_audit_action,
    invalidate_employee_cache,
    get_active_employee_nums,
)

router = APIRouter(prefix="/api/yukyu", tags=["Yukyu Details"])


# ============================================
# PYDANTIC MODELS
# ============================================

class UsageDetailUpdate(BaseModel):
    """Model for updating a yukyu usage record."""
    days_used: Optional[float] = Field(None, ge=0.25, le=1.0, description="Days used (0.25, 0.5, 1.0)")
    use_date: Optional[str] = Field(None, description="New date YYYY-MM-DD")

    @field_validator('days_used')
    @classmethod
    def validate_days(cls, v):
        if v is not None:
            valid_values = [0.25, 0.5, 0.75, 1.0]
            if v not in valid_values:
                raise ValueError(f'days_used must be: {valid_values} (0.5 = half day)')
        return v


class UsageDetailCreate(BaseModel):
    """Model for creating a new yukyu usage record."""
    employee_num: str = Field(..., min_length=1, description="Employee number")
    name: str = Field(..., min_length=1, description="Employee name")
    use_date: str = Field(..., description="Usage date YYYY-MM-DD")
    days_used: float = Field(1.0, ge=0.25, le=1.0, description="Days used")

    @field_validator('days_used')
    @classmethod
    def validate_days(cls, v):
        valid_values = [0.25, 0.5, 0.75, 1.0]
        if v not in valid_values:
            raise ValueError(f'days_used must be: {valid_values}')
        return v


# ============================================
# USAGE DETAILS ENDPOINTS
# ============================================

@router.get("/usage-details")
async def get_usage_details(
    employee_num: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """
    Get yukyu usage details with optional filters.
    Obtiene detalles de uso de vacaciones con filtros opcionales.
    """
    try:
        details = database.get_yukyu_usage_details(
            employee_num=employee_num,
            year=year,
            month=month
        )
        return {
            "status": "success",
            "count": len(details),
            "data": details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monthly-summary/{year}")
async def get_monthly_summary(year: int):
    """
    Get monthly usage summary for a year.
    Obtiene resumen mensual de uso para un ano.
    """
    try:
        summary = database.get_monthly_usage_summary(year)
        return {
            "status": "success",
            "year": year,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpi-stats/{year}")
async def get_kpi_stats(year: int):
    """
    Get KPI statistics for a year.
    Obtiene estadisticas KPI para un ano.
    """
    try:
        employees = database.get_employees(year=year)

        total_granted = sum(e.get('granted', 0) for e in employees)
        total_used = sum(e.get('used', 0) for e in employees)
        total_balance = sum(e.get('balance', 0) for e in employees)

        usage_rate = (total_used / total_granted * 100) if total_granted > 0 else 0

        return {
            "status": "success",
            "year": year,
            "kpi": {
                "total_employees": len(employees),
                "total_granted": round(total_granted, 1),
                "total_used": round(total_used, 1),
                "total_balance": round(total_balance, 1),
                "usage_rate": round(usage_rate, 1),
                "avg_granted": round(total_granted / len(employees), 1) if employees else 0,
                "avg_used": round(total_used / len(employees), 1) if employees else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-employee-type/{year}")
async def get_usage_by_employee_type(year: int, active_only: bool = True):
    """
    Get usage statistics broken down by employee type.
    Obtiene estadisticas de uso desglosadas por tipo de empleado.
    """
    try:
        employees = database.get_employees(year=year)

        genzai_list = database.get_genzai(status='在職中' if active_only else None)
        ukeoi_list = database.get_ukeoi(status='在職中' if active_only else None)
        staff_list = database.get_staff(status='在職中' if active_only else None)

        genzai_nums = {str(emp['employee_num']) for emp in genzai_list if emp.get('employee_num')}
        ukeoi_nums = {str(emp['employee_num']) for emp in ukeoi_list if emp.get('employee_num')}
        staff_nums = {str(emp['employee_num']) for emp in staff_list if emp.get('employee_num')}

        stats = {
            'haken': {'count': 0, 'granted': 0, 'used': 0, 'balance': 0},
            'ukeoi': {'count': 0, 'granted': 0, 'used': 0, 'balance': 0},
            'staff': {'count': 0, 'granted': 0, 'used': 0, 'balance': 0},
            'unknown': {'count': 0, 'granted': 0, 'used': 0, 'balance': 0}
        }

        for emp in employees:
            emp_num = str(emp.get('employee_num', ''))

            if emp_num in genzai_nums:
                emp_type = 'haken'
            elif emp_num in ukeoi_nums:
                emp_type = 'ukeoi'
            elif emp_num in staff_nums:
                emp_type = 'staff'
            else:
                emp_type = 'unknown'

            stats[emp_type]['count'] += 1
            stats[emp_type]['granted'] += emp.get('granted', 0)
            stats[emp_type]['used'] += emp.get('used', 0)
            stats[emp_type]['balance'] += emp.get('balance', 0)

        # Calculate rates
        for type_stats in stats.values():
            if type_stats['granted'] > 0:
                type_stats['usage_rate'] = round(
                    type_stats['used'] / type_stats['granted'] * 100, 1
                )
            else:
                type_stats['usage_rate'] = 0

        return {
            "status": "success",
            "year": year,
            "active_only": active_only,
            "by_type": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/employee-summary/{employee_num}/{year}")
async def get_employee_summary(employee_num: str, year: int):
    """
    Get detailed usage summary for a specific employee.
    Obtiene resumen detallado de uso para un empleado especifico.
    """
    try:
        # Get employee data
        employees = database.get_employees(year=year)
        employee = next(
            (e for e in employees if str(e.get('employee_num')) == employee_num),
            None
        )

        if not employee:
            raise HTTPException(
                status_code=404,
                detail=f"Employee {employee_num} not found for year {year}"
            )

        # Get usage details
        usage_details = database.get_yukyu_usage_details(
            employee_num=employee_num,
            year=year
        )

        # Get history
        history = database.get_employee_yukyu_history(employee_num, year)

        return {
            "status": "success",
            "employee": employee,
            "usage_details": usage_details,
            "history": history,
            "summary": {
                "total_granted": employee.get('granted', 0),
                "total_used": employee.get('used', 0),
                "balance": employee.get('balance', 0),
                "usage_count": len(usage_details)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/usage-details/{detail_id}")
async def update_usage_detail(
    request: Request,
    detail_id: int,
    update_data: UsageDetailUpdate,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Update a yukyu usage detail record.
    Actualiza un registro de uso de vacaciones.
    """
    try:
        # Get old value
        old_detail = database.get_usage_detail_by_id(detail_id)
        if not old_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Usage detail {detail_id} not found"
            )

        updates = {}
        if update_data.days_used is not None:
            updates['days_used'] = update_data.days_used
        if update_data.use_date is not None:
            updates['use_date'] = update_data.use_date

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updated = database.update_yukyu_usage_detail(detail_id, updates)
        invalidate_employee_cache()

        # Audit log
        await log_audit_action(
            request=request,
            action="UPDATE",
            entity_type="yukyu_usage",
            entity_id=str(detail_id),
            old_value=old_detail,
            new_value=updated,
            user=user
        )

        logger.info(f"Usage detail {detail_id} updated by {user.username}")

        return {
            "status": "success",
            "message": "Usage detail updated",
            "updated_record": updated
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/usage-details/{detail_id}")
async def delete_usage_detail(
    request: Request,
    detail_id: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Delete a yukyu usage detail record.
    Elimina un registro de uso de vacaciones.
    """
    try:
        # Get old value
        old_detail = database.get_usage_detail_by_id(detail_id)
        if not old_detail:
            raise HTTPException(
                status_code=404,
                detail=f"Usage detail {detail_id} not found"
            )

        database.delete_yukyu_usage_detail(detail_id)
        invalidate_employee_cache()

        # Audit log
        await log_audit_action(
            request=request,
            action="DELETE",
            entity_type="yukyu_usage",
            entity_id=str(detail_id),
            old_value=old_detail,
            user=user
        )

        logger.info(f"Usage detail {detail_id} deleted by {user.username}")

        return {
            "status": "success",
            "message": f"Usage detail {detail_id} deleted",
            "deleted_record": old_detail
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/usage-details")
async def create_usage_detail(
    request: Request,
    detail_data: UsageDetailCreate,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Create a new yukyu usage detail record.
    Crea un nuevo registro de uso de vacaciones.
    """
    try:
        # Parse year from use_date
        use_date = datetime.strptime(detail_data.use_date, '%Y-%m-%d')
        year = use_date.year

        new_id = database.create_yukyu_usage_detail(
            employee_num=detail_data.employee_num,
            name=detail_data.name,
            use_date=detail_data.use_date,
            days_used=detail_data.days_used,
            year=year
        )

        invalidate_employee_cache()

        # Audit log
        await log_audit_action(
            request=request,
            action="CREATE",
            entity_type="yukyu_usage",
            entity_id=str(new_id),
            new_value=detail_data.model_dump(),
            user=user
        )

        logger.info(f"Usage detail created by {user.username}: {new_id}")

        return {
            "status": "success",
            "message": "Usage detail created",
            "detail_id": new_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recalculate/{employee_num}/{year}")
async def recalculate_employee_totals(
    request: Request,
    employee_num: str,
    year: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Recalculate employee totals from usage details.
    Recalcula los totales del empleado desde los detalles de uso.
    """
    try:
        # Get current data
        old_data = database.get_employee_by_num_year(employee_num, year)

        # Recalculate
        result = database.recalculate_employee_from_details(employee_num, year)
        invalidate_employee_cache()

        # Audit log
        await log_audit_action(
            request=request,
            action="RECALCULATE",
            entity_type="employee",
            entity_id=f"{employee_num}_{year}",
            old_value=old_data,
            new_value=result,
            user=user
        )

        logger.info(f"Employee {employee_num} recalculated by {user.username}")

        return {
            "status": "success",
            "message": f"Recalculated totals for {employee_num}",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
