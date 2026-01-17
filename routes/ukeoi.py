"""
Ukeoi (Contract Employees) Routes
Endpoints de empleados contratistas (請負社員)
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

router = APIRouter(prefix="/api", tags=["Ukeoi"])

# Thread pool for Excel parsing
_excel_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ukeoi_parser")


@router.get("/ukeoi")
async def get_ukeoi(status: str = None):
    """
    Get ukeoi (contract) employees.
    Obtiene empleados contratistas (請負社員).
    """
    try:
        data = database.get_ukeoi(status=status)
        return {"status": "success", "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"Failed to get ukeoi: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sync-ukeoi")
async def sync_ukeoi(user: CurrentUser = Depends(get_current_user)):
    """
    Sync ukeoi data from employee registry Excel.
    Sincroniza datos de ukeoi desde Excel de registro de empleados.
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
            excel_service.parse_ukeoi_sheet,
            EMPLOYEE_REGISTRY_PATH
        )

        database.save_ukeoi(data)

        log_sync_event("SYNC_UKEOI", {
            "count": len(data),
            "user": user.username if user else None
        })

        logger.info(f"Synced {len(data)} ukeoi employees")

        return {
            "status": "success",
            "message": f"Synced {len(data)} ukeoi employees",
            "count": len(data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync ukeoi error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/reset-ukeoi")
async def reset_ukeoi(user: CurrentUser = Depends(get_admin_user)):
    """
    Clear all ukeoi data from database.
    Requires admin authentication.

    Elimina todos los datos de ukeoi de la base de datos.
    """
    try:
        database.reset_ukeoi()
        logger.info(f"Ukeoi data reset by {user.username}")
        return {"status": "success", "message": "All ukeoi data has been cleared"}
    except Exception as e:
        logger.error(f"Failed to reset ukeoi: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
