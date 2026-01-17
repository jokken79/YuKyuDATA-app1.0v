"""
Staff (Office Employees) Routes
Endpoints de personal de oficina
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    database,
    logger,
    log_sync_event,
    EMPLOYEE_REGISTRY_PATH,
)
import excel_service

router = APIRouter(prefix="/api", tags=["Staff"])

# Thread pool for Excel parsing
_excel_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="staff_parser")


@router.get("/staff")
async def get_staff(status: str = None):
    """
    Get staff (office) employees.
    Obtiene personal de oficina.
    """
    try:
        data = database.get_staff(status=status)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Failed to get staff: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sync-staff")
async def sync_staff(user: CurrentUser = Depends(get_current_user)):
    """
    Sync staff data from employee registry Excel.
    Sincroniza datos de staff desde Excel de registro de empleados.
    """
    try:
        if not EMPLOYEE_REGISTRY_PATH.exists():
            logger.error(f"Employee registry not found: {EMPLOYEE_REGISTRY_PATH}")
            raise HTTPException(
                status_code=404,
                detail="Employee registry file not found"
            )

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            _excel_executor,
            excel_service.parse_staff_sheet,
            EMPLOYEE_REGISTRY_PATH
        )

        database.save_staff(data)

        log_sync_event("SYNC_STAFF", {
            "count": len(data),
            "user": user.username if user else None
        })

        logger.info(f"Synced {len(data)} staff employees")

        return {
            "status": "success",
            "message": f"Synced {len(data)} staff employees",
            "count": len(data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync staff error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/reset-staff")
async def reset_staff(user: CurrentUser = Depends(get_admin_user)):
    """
    Clear all staff data from database.
    Requires admin authentication.

    Elimina todos los datos de staff de la base de datos.
    """
    try:
        database.reset_staff()
        logger.info(f"Staff data reset by {user.username}")
        return {"status": "success", "message": "All staff data has been cleared"}
    except Exception as e:
        logger.error(f"Failed to reset staff: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
