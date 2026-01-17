"""
Genzai (Dispatch Employees) Routes
Endpoints de empleados de despacho (派遣社員)
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
from services import excel_service

router = APIRouter(prefix="/api", tags=["Genzai"])

# Thread pool for Excel parsing
_excel_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="genzai_parser")


@router.get("/genzai")
async def get_genzai(status: str = None):
    """
    Get genzai (dispatch) employees.
    Obtiene empleados de despacho (派遣社員).
    """
    try:
        data = database.get_genzai(status=status)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Failed to get genzai: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sync-genzai")
async def sync_genzai(user: CurrentUser = Depends(get_current_user)):
    """
    Sync genzai data from employee registry Excel.
    Sincroniza datos de genzai desde Excel de registro de empleados.
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
            excel_service.parse_genzai_sheet,
            EMPLOYEE_REGISTRY_PATH
        )

        database.save_genzai(data)

        log_sync_event("SYNC_GENZAI", {
            "count": len(data),
            "user": user.username if user else None
        })

        logger.info(f"Synced {len(data)} genzai employees")

        return {
            "status": "success",
            "message": f"Synced {len(data)} genzai employees",
            "count": len(data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync genzai error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/reset-genzai")
async def reset_genzai(user: CurrentUser = Depends(get_admin_user)):
    """
    Clear all genzai data from database.
    Requires admin authentication.

    Elimina todos los datos de genzai de la base de datos.
    """
    try:
        database.reset_genzai()
        logger.info(f"Genzai data reset by {user.username}")
        return {"status": "success", "message": "All genzai data has been cleared"}
    except Exception as e:
        logger.error(f"Failed to reset genzai: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
