"""
Analytics Routes
Endpoints de analisis y KPIs
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime

from ..dependencies import (
    get_current_user,
    CurrentUser,
    database,
    logger,
    get_active_employee_nums,
)

router = APIRouter(prefix="", tags=["Analytics"])


# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@router.get("/stats/by-factory")
async def get_stats_by_factory(
    year: int = Query(None, ge=2000, le=2100),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get statistics grouped by factory/haken.
    Obtiene estadisticas agrupadas por fabrica/haken.
    """
    try:
        if year is None:
            year = datetime.now().year

        employees = database.get_employees(year=year)

        # Group by haken
        factory_stats = {}
        for emp in employees:
            haken = emp.get('haken', 'Unknown')
            if haken not in factory_stats:
                factory_stats[haken] = {
                    'count': 0,
                    'total_granted': 0,
                    'total_used': 0,
                    'total_balance': 0
                }
            factory_stats[haken]['count'] += 1
            factory_stats[haken]['total_granted'] += emp.get('granted', 0)
            factory_stats[haken]['total_used'] += emp.get('used', 0)
            factory_stats[haken]['total_balance'] += emp.get('balance', 0)

        # Calculate averages and rates
        for haken, stats in factory_stats.items():
            if stats['count'] > 0:
                stats['avg_granted'] = round(stats['total_granted'] / stats['count'], 1)
                stats['avg_used'] = round(stats['total_used'] / stats['count'], 1)
            if stats['total_granted'] > 0:
                stats['usage_rate'] = round(stats['total_used'] / stats['total_granted'] * 100, 1)
            else:
                stats['usage_rate'] = 0

        return {
            "status": "success",
            "year": year,
            "factories": factory_stats
        }
    except Exception as e:
        logger.error(f"Analytics operation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/factories")
async def get_factories(
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get list of unique factories/haken values.
    Obtiene lista de valores unicos de fabricas/haken.
    """
    try:
        employees = database.get_employees()
        factories = list(set(
            emp.get('haken', 'Unknown')
            for emp in employees
            if emp.get('haken')
        ))
        factories.sort()

        return {
            "status": "success",
            "count": len(factories),
            "factories": factories
        }
    except Exception as e:
        logger.error(f"Analytics operation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/top10-active/{year}")
async def get_top10_active_users(
    year: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get top 10 active users (only 在職中).
    Excludes employees who have resigned.

    Obtiene el Top 10 de usuarios activos (solo 在職中).
    Excluye empleados que ya renunciaron.
    """
    try:
        active_nums = get_active_employee_nums()
        employees = database.get_employees(year=year)

        # Filter active only
        active_employees = [
            emp for emp in employees
            if str(emp.get('employee_num', '')) in active_nums
        ]

        # Sort by used days descending
        sorted_employees = sorted(
            active_employees,
            key=lambda x: x.get('used', 0),
            reverse=True
        )[:10]

        return {
            "status": "success",
            "year": year,
            "top10": [
                {
                    "rank": i + 1,
                    "employee_num": emp['employee_num'],
                    "name": emp['name'],
                    "haken": emp.get('haken', ''),
                    "used": emp.get('used', 0),
                    "granted": emp.get('granted', 0),
                    "balance": emp.get('balance', 0)
                }
                for i, emp in enumerate(sorted_employees)
            ]
        }
    except Exception as e:
        logger.error(f"Analytics operation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/high-balance-active/{year}")
async def get_high_balance_active(
    year: int,
    min_balance: float = Query(20, ge=0, le=100),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get active employees with high balance.
    Useful for identifying employees who should be encouraged to use leave.

    Obtiene empleados activos con balance alto.
    """
    try:
        active_nums = get_active_employee_nums()
        employees = database.get_employees(year=year)

        high_balance = [
            emp for emp in employees
            if str(emp.get('employee_num', '')) in active_nums
            and emp.get('balance', 0) >= min_balance
        ]

        # Sort by balance descending
        high_balance.sort(key=lambda x: x.get('balance', 0), reverse=True)

        return {
            "status": "success",
            "year": year,
            "min_balance": min_balance,
            "count": len(high_balance),
            "employees": [
                {
                    "employee_num": emp['employee_num'],
                    "name": emp['name'],
                    "haken": emp.get('haken', ''),
                    "balance": emp.get('balance', 0),
                    "granted": emp.get('granted', 0),
                    "used": emp.get('used', 0)
                }
                for emp in high_balance
            ]
        }
    except Exception as e:
        logger.error(f"Analytics operation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/dashboard/{year}")
async def get_dashboard_analytics(
    year: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get comprehensive dashboard analytics.
    Obtiene analiticas completas para el dashboard.
    """
    try:
        employees = database.get_employees(year=year)
        active_nums = get_active_employee_nums()

        # Filter to active only
        active_employees = [
            emp for emp in employees
            if str(emp.get('employee_num', '')) in active_nums
        ]

        # Basic stats
        total_granted = sum(e.get('granted', 0) for e in active_employees)
        total_used = sum(e.get('used', 0) for e in active_employees)
        total_balance = sum(e.get('balance', 0) for e in active_employees)

        # Usage rate
        overall_rate = (total_used / total_granted * 100) if total_granted > 0 else 0

        # Distribution by usage rate
        low_usage = sum(1 for e in active_employees if e.get('usage_rate', 0) < 25)
        mid_usage = sum(1 for e in active_employees if 25 <= e.get('usage_rate', 0) < 75)
        high_usage = sum(1 for e in active_employees if e.get('usage_rate', 0) >= 75)

        # 5-day compliance
        below_5days = sum(1 for e in active_employees if e.get('used', 0) < 5)
        at_5days = sum(1 for e in active_employees if e.get('used', 0) >= 5)

        # By factory
        factory_stats = {}
        for emp in active_employees:
            haken = emp.get('haken', 'Unknown')
            if haken not in factory_stats:
                factory_stats[haken] = {'count': 0, 'used': 0, 'granted': 0}
            factory_stats[haken]['count'] += 1
            factory_stats[haken]['used'] += emp.get('used', 0)
            factory_stats[haken]['granted'] += emp.get('granted', 0)

        return {
            "status": "success",
            "year": year,
            "summary": {
                "total_employees": len(active_employees),
                "total_granted": round(total_granted, 1),
                "total_used": round(total_used, 1),
                "total_balance": round(total_balance, 1),
                "overall_usage_rate": round(overall_rate, 1)
            },
            "usage_distribution": {
                "low_usage": low_usage,
                "mid_usage": mid_usage,
                "high_usage": high_usage
            },
            "compliance": {
                "below_5days": below_5days,
                "at_or_above_5days": at_5days,
                "compliance_rate": round(at_5days / len(active_employees) * 100, 1) if active_employees else 0
            },
            "by_factory": factory_stats
        }
    except Exception as e:
        logger.error(f"Analytics operation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/monthly-trend/{year}")
async def get_monthly_trend(
    year: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get monthly usage trend for a year.
    Obtiene tendencia mensual de uso para un ano.
    """
    try:
        # Get usage details by month
        monthly_data = {}
        for month in range(1, 13):
            usage = database.get_yukyu_usage_details(year=year, month=month)
            monthly_data[month] = {
                'month': month,
                'usage_count': len(usage),
                'total_days': sum(u.get('days_used', 0) for u in usage)
            }

        return {
            "status": "success",
            "year": year,
            "monthly_trend": list(monthly_data.values())
        }
    except Exception as e:
        logger.error(f"Analytics operation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/predictions/{year}")
async def get_usage_predictions(
    year: int,
    user: CurrentUser = Depends(get_current_user)
):
    """
    Get usage predictions based on historical data.
    Obtiene predicciones de uso basadas en datos historicos.
    """
    try:
        employees = database.get_employees(year=year)

        # Calculate current month
        current_month = datetime.now().month
        months_passed = current_month
        months_remaining = 12 - current_month

        predictions = []
        for emp in employees:
            used = emp.get('used', 0)
            balance = emp.get('balance', 0)

            # Projected annual usage
            if months_passed > 0:
                monthly_rate = used / months_passed
                projected_total = used + (monthly_rate * months_remaining)
            else:
                monthly_rate = 0
                projected_total = 0

            # Risk assessment
            if balance > 0 and months_remaining > 0:
                needed_per_month = (5 - used) / months_remaining if used < 5 else 0
                risk_level = 'high' if needed_per_month > 1 else 'low' if needed_per_month <= 0 else 'medium'
            else:
                needed_per_month = 0
                risk_level = 'compliant' if used >= 5 else 'high'

            predictions.append({
                'employee_num': emp['employee_num'],
                'name': emp['name'],
                'current_used': used,
                'balance': balance,
                'monthly_rate': round(monthly_rate, 2),
                'projected_annual': round(projected_total, 1),
                'needed_per_month_for_5days': round(needed_per_month, 2),
                'risk_level': risk_level
            })

        # Sort by risk
        risk_order = {'high': 0, 'medium': 1, 'low': 2, 'compliant': 3}
        predictions.sort(key=lambda x: risk_order.get(x['risk_level'], 4))

        return {
            "status": "success",
            "year": year,
            "current_month": current_month,
            "months_remaining": months_remaining,
            "predictions": predictions,
            "summary": {
                "high_risk": sum(1 for p in predictions if p['risk_level'] == 'high'),
                "medium_risk": sum(1 for p in predictions if p['risk_level'] == 'medium'),
                "low_risk": sum(1 for p in predictions if p['risk_level'] == 'low'),
                "compliant": sum(1 for p in predictions if p['risk_level'] == 'compliant')
            }
        }
    except Exception as e:
        logger.error(f"Analytics operation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
