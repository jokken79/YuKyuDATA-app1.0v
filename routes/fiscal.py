"""
Fiscal Year Routes
Endpoints de operaciones del ano fiscal
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from .dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    database,
    logger,
    FISCAL_CONFIG,
    GRANT_TABLE,
    process_year_end_carryover,
    get_employee_balance_breakdown,
    check_expiring_soon,
    check_5day_compliance,
    get_grant_recommendation,
    apply_lifo_deduction,
)

router = APIRouter(prefix="/api/fiscal", tags=["Fiscal Year"])


# ============================================
# PYDANTIC MODELS
# ============================================

class FifoDeductionRequest(BaseModel):
    """Model for FIFO deduction request."""
    employee_num: str = Field(..., min_length=1)
    days: float = Field(..., gt=0, le=40)
    year: int = Field(..., ge=2000, le=2100)


class CarryoverRequest(BaseModel):
    """Model for year-end carryover request."""
    from_year: int = Field(..., ge=2000, le=2100)
    to_year: int = Field(..., ge=2000, le=2100)


# ============================================
# FISCAL YEAR ENDPOINTS
# ============================================

@router.get("/config")
async def get_fiscal_config():
    """
    Get fiscal year configuration.
    Obtiene la configuracion del ano fiscal.
    """
    return {
        "status": "success",
        "config": FISCAL_CONFIG,
        "grant_table": GRANT_TABLE
    }


@router.post("/process-carryover")
async def process_carryover(
    request: CarryoverRequest,
    user: CurrentUser = Depends(get_admin_user)
):
    """
    Process year-end carryover.
    Procesa el traspaso de fin de ano.

    Requires admin authentication.
    """
    try:
        result = process_year_end_carryover(request.from_year, request.to_year)
        logger.info(f"Carryover processed by {user.username}: {request.from_year} -> {request.to_year}")

        return {
            "status": "success",
            "from_year": request.from_year,
            "to_year": request.to_year,
            "result": result
        }
    except Exception as e:
        logger.error(f"Carryover error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance-breakdown/{employee_num}")
async def get_balance_breakdown(employee_num: str, year: Optional[int] = None):
    """
    Get detailed balance breakdown for an employee.
    Shows balance by grant year (LIFO order).

    Obtiene desglose detallado del balance de un empleado.
    """
    try:
        if year is None:
            year = datetime.now().year

        breakdown = get_employee_balance_breakdown(employee_num, year)

        return {
            "status": "success",
            "employee_num": employee_num,
            "year": year,
            "breakdown": breakdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring-soon")
async def get_expiring_soon(
    year: Optional[int] = None,
    threshold_months: int = 3
):
    """
    Get employees with days expiring soon.
    Obtiene empleados con dias que estan por vencer.
    """
    try:
        if year is None:
            year = datetime.now().year

        expiring = check_expiring_soon(year, threshold_months)

        return {
            "status": "success",
            "year": year,
            "threshold_months": threshold_months,
            "count": len(expiring),
            "employees": expiring
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/5day-compliance/{year}")
async def get_5day_compliance(year: int):
    """
    Check 5-day compliance for all employees.
    Verifica cumplimiento de 5 dias para todos los empleados.
    """
    try:
        compliance = check_5day_compliance(year)
        return {
            "status": "success",
            "year": year,
            "compliance": compliance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grant-recommendation/{employee_num}")
async def get_grant_recommendation_endpoint(employee_num: str):
    """
    Get grant recommendation for an employee based on seniority.
    Obtiene recomendacion de otorgamiento basada en antiguedad.
    """
    try:
        recommendation = get_grant_recommendation(employee_num)
        return {
            "status": "success",
            "employee_num": employee_num,
            "recommendation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-fifo-deduction")
async def apply_fifo_deduction_endpoint(
    request: FifoDeductionRequest,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Apply FIFO (actually LIFO) deduction to an employee's balance.
    Deducts from newest grant periods first.

    Aplica deduccion FIFO (en realidad LIFO) al balance de un empleado.
    """
    try:
        result = apply_lifo_deduction(
            request.employee_num,
            request.days,
            request.year
        )

        logger.info(
            f"LIFO deduction by {user.username}: "
            f"{request.employee_num} - {request.days} days for year {request.year}"
        )

        return {
            "status": "success",
            "employee_num": request.employee_num,
            "days_deducted": request.days,
            "year": request.year,
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LIFO deduction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
