"""
System Routes
Endpoints de sistema, backup, audit log, cache, orchestrator
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta, timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    database,
    logger,
    get_cache_stats,
    invalidate_employee_cache,
    DEFAULT_EXCEL_PATH,
)
from services import excel_service
from services.excel_export import update_master_excel

router = APIRouter(prefix="", tags=["System"])

# Thread pool for Excel operations
_excel_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="system_excel")


# ============================================
# CACHE ENDPOINTS
# ============================================

@router.get("/cache-stats")
async def get_cache_statistics():
    """Get cache statistics."""
    try:
        stats = get_cache_stats()
        return {"status": "success", "cache_stats": stats}
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/cache/clear")
async def clear_cache(user: CurrentUser = Depends(get_current_user)):
    """Clear all caches."""
    try:
        invalidate_employee_cache()
        logger.info(f"Cache cleared by {user.username}")
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# BACKUP ENDPOINTS
# ============================================

@router.post("/backup")
async def create_backup(user: CurrentUser = Depends(get_admin_user)):
    """
    Create a database backup.
    Backups are saved in the 'backups/' folder.
    Only the last 10 backups are kept.
    Requires admin authentication.

    Crea una copia de seguridad de la base de datos.
    """
    try:
        result = database.create_backup()
        logger.info(f"Backup created by {user.username}: {result['filename']}")

        return {
            "status": "success",
            "message": f"Backup created: {result['filename']}",
            "backup": result
        }
    except Exception as e:
        logger.error(f"Backup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/backups")
async def list_backups(user: CurrentUser = Depends(get_current_user)):
    """List all available backups. Requires authentication."""
    try:
        backups = database.list_backups()
        return {
            "status": "success",
            "count": len(backups),
            "backups": backups
        }
    except Exception as e:
        logger.error(f"Failed to list backups: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/backup/restore")
async def restore_backup(restore_data: dict, user: CurrentUser = Depends(get_admin_user)):
    """
    Restore database from a backup.
    WARNING: This overwrites the current database.
    An automatic backup is created before restoring.

    Restaura la base de datos desde un backup.
    """
    try:
        filename = restore_data.get('filename')
        if not filename:
            raise HTTPException(status_code=400, detail="filename is required")

        result = database.restore_backup(filename)
        logger.info(f"Backup restored: {result}")

        return {
            "status": "success",
            "message": f"Database restored from {filename}",
            "restore": result
        }
    except ValueError as ve:
        logger.warning(f"Restore validation error: {str(ve)}")
        raise HTTPException(status_code=400, detail="Invalid restore request")
    except Exception as e:
        logger.error(f"Restore error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# AUDIT LOG ENDPOINTS
# ============================================

@router.get("/audit-log")
async def get_audit_log_list(
    request: Request,
    entity_type: str = None,
    entity_id: str = None,
    action: str = None,
    user_id: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """
    Get audit log entries with optional filters.
    Obtiene entradas del audit log con filtros opcionales.
    """
    try:
        logs = database.get_audit_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        return {
            "status": "success",
            "count": len(logs),
            "offset": offset,
            "limit": limit,
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Failed to get audit log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audit-log/{entity_type}/{entity_id}")
async def get_entity_audit_history(entity_type: str, entity_id: str):
    """Get audit history for a specific entity."""
    try:
        logs = database.get_audit_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=100
        )

        return {
            "status": "success",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "count": len(logs),
            "history": logs
        }
    except Exception as e:
        logger.error(f"Failed to get entity audit history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audit-log/user/{user_id}")
async def get_user_audit_history(user_id: str, limit: int = 50):
    """Get audit history for a specific user."""
    try:
        logs = database.get_audit_logs(user_id=user_id, limit=limit)

        return {
            "status": "success",
            "user_id": user_id,
            "count": len(logs),
            "history": logs
        }
    except Exception as e:
        logger.error(f"Failed to get user audit history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audit-log/stats")
async def get_audit_log_stats():
    """Get audit log statistics."""
    try:
        stats = database.get_audit_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get audit log stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/audit-log/cleanup")
async def cleanup_audit_log(
    days_to_keep: int = Query(default=90, ge=1, le=365),
    user: CurrentUser = Depends(get_admin_user)
):
    """
    Delete old audit log entries.
    Requires admin authentication.

    Elimina entradas antiguas del audit log.
    """
    try:
        deleted_count = database.cleanup_audit_log(days_to_keep)
        logger.info(f"Audit log cleanup by {user.username}: {deleted_count} entries deleted")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "days_threshold": days_to_keep
        }
    except Exception as e:
        logger.error(f"Failed to cleanup audit log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# ORCHESTRATOR ENDPOINTS
# ============================================

@router.get("/orchestrator/status")
async def get_orchestrator_status():
    """Get orchestrator status."""
    try:
        from agents.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        status = orchestrator.get_status()
        return {"status": "success", "orchestrator": status}
    except Exception as e:
        logger.error(f"Failed to get orchestrator status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/orchestrator/history")
async def get_orchestrator_history(limit: int = 20):
    """Get orchestrator execution history."""
    try:
        from agents.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        history = orchestrator.get_history(limit)
        return {
            "status": "success",
            "count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Failed to get orchestrator history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/orchestrator/run-compliance-check/{year}")
async def run_orchestrator_compliance_check(year: int):
    """
    Run compliance check via orchestrator.
    Ejecuta verificacion de compliance via orchestrator.
    """
    try:
        from agents.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        result = orchestrator.run_compliance_check(year)
        return {
            "status": "success",
            "year": year,
            "result": result
        }
    except Exception as e:
        logger.error(f"Failed to run orchestrator compliance check: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# SYSTEM SNAPSHOT ENDPOINTS
# ============================================

@router.get("/system/snapshot")
async def get_system_snapshot():
    """Get current system snapshot."""
    try:
        from agents.documentor import get_documentor
        documentor = get_documentor()
        snapshot = documentor.create_snapshot()
        return {"status": "success", "snapshot": snapshot.to_dict()}
    except Exception as e:
        logger.error(f"Failed to get system snapshot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/system/audit-log")
async def get_system_audit_log(limit: int = 50):
    """Get recent system audit log entries."""
    try:
        from agents.documentor import get_documentor
        documentor = get_documentor()
        entries = documentor.get_recent_entries(limit)
        return {
            "status": "success",
            "count": len(entries),
            "entries": [e.to_dict() for e in entries]
        }
    except Exception as e:
        logger.error(f"Failed to get system audit log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/system/activity-report")
async def get_activity_report(days: int = 7):
    """
    Generate an activity report for the last N days.
    Genera un reporte de actividad para los ultimos N dias.
    """
    try:
        from agents.documentor import get_documentor
        documentor = get_documentor()

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        report = documentor.generate_activity_report(
            start_date.isoformat(),
            end_date.isoformat()
        )
        return {"status": "success", "report": report.to_dict()}
    except Exception as e:
        logger.error(f"Failed to get activity report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# SYNC MASTER EXCEL ENDPOINT
# ============================================

@router.post("/sync/update-master-excel")
async def update_master_excel_endpoint(user: CurrentUser = Depends(get_admin_user)):
    """
    Update the master Excel file with changes from database.
    Writes approved leave requests back to the Excel file.
    Requires admin authentication.

    Actualiza el archivo Excel maestro con cambios de la base de datos.
    """
    try:
        if not DEFAULT_EXCEL_PATH.exists():
            logger.error(f"Master Excel not found: {DEFAULT_EXCEL_PATH}")
            raise HTTPException(
                status_code=404,
                detail="Master Excel file not found"
            )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _excel_executor,
            update_master_excel,
            str(DEFAULT_EXCEL_PATH)
        )

        logger.info(f"Master Excel updated by {user.username}: {result}")

        return {
            "status": "success",
            "message": "Master Excel updated",
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating master Excel: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
