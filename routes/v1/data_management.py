"""
Data Management Routes
Endpoints para upload de Excel y control de base de datos
"""

from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File, Form
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..dependencies import (
    get_current_user,
    get_admin_user,
    CurrentUser,
    database,
    logger,
    log_sync_event,
    log_audit_action,
    invalidate_employee_cache,
    UPLOAD_DIR,
)
from services import excel_service
from utils.file_validator import validate_excel_file, sanitize_filename

router = APIRouter(prefix="/data-management", tags=["Data Management"])

_excel_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="dm_excel")

ALLOWED_RESET_TABLES = {'employees', 'genzai', 'ukeoi', 'staff', 'yukyu_usage_details'}


@router.post("/upload")
async def upload_data_file(
    request: Request,
    file: UploadFile = File(...),
    type: str = Form(...),
    user: CurrentUser = Depends(get_current_user)
):
    """
    Upload and process Excel file by type.
    - type=yukyu: parses employees + usage details from 有給休暇管理
    - type=shaintaicho: parses genzai, ukeoi, staff from 社員台帳
    """
    if type not in ('yukyu', 'shaintaicho'):
        raise HTTPException(status_code=400, detail="Invalid type. Must be 'yukyu' or 'shaintaicho'")

    try:
        file_content = await validate_excel_file(file)
        sanitized_name = sanitize_filename(file.filename)
        upload_path = UPLOAD_DIR / sanitized_name

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        with open(upload_path, "wb") as buffer:
            buffer.write(file_content)

        loop = asyncio.get_event_loop()
        result = {}

        if type == 'yukyu':
            data = await loop.run_in_executor(
                _excel_executor,
                excel_service.parse_excel_file,
                upload_path
            )
            database.save_employees(data)
            invalidate_employee_cache()

            usage_details = []
            try:
                usage_details = await loop.run_in_executor(
                    _excel_executor,
                    excel_service.parse_yukyu_usage_details,
                    upload_path
                )
                database.save_yukyu_usage_details(usage_details)
            except Exception as e:
                logger.warning(f"Could not parse usage details: {e}")

            result = {
                "employees": len(data),
                "usage_details": len(usage_details),
            }

            log_sync_event("DM_UPLOAD_YUKYU", {
                "filename": file.filename,
                "employees": len(data),
                "usage_details": len(usage_details),
                "user": user.username,
            })

        elif type == 'shaintaicho':
            genzai_data = await loop.run_in_executor(
                _excel_executor,
                excel_service.parse_genzai_sheet,
                upload_path
            )
            database.save_genzai(genzai_data)

            ukeoi_data = await loop.run_in_executor(
                _excel_executor,
                excel_service.parse_ukeoi_sheet,
                upload_path
            )
            database.save_ukeoi(ukeoi_data)

            staff_data = await loop.run_in_executor(
                _excel_executor,
                excel_service.parse_staff_sheet,
                upload_path
            )
            database.save_staff(staff_data)

            invalidate_employee_cache()

            result = {
                "genzai": len(genzai_data),
                "ukeoi": len(ukeoi_data),
                "staff": len(staff_data),
            }

            log_sync_event("DM_UPLOAD_SHAINTAICHO", {
                "filename": file.filename,
                "genzai": len(genzai_data),
                "ukeoi": len(ukeoi_data),
                "staff": len(staff_data),
                "user": user.username,
            })

        await log_audit_action(
            request=request,
            action="UPLOAD",
            entity_type="data_management",
            entity_id=type,
            new_value=result,
            user=user,
        )

        logger.info(f"Data management upload ({type}) by {user.username}: {result}")

        return {
            "status": "success",
            "type": type,
            "message": f"Upload successful",
            "result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data management upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/table-counts")
async def get_table_counts(user: CurrentUser = Depends(get_current_user)):
    """Get row counts for all main data tables."""
    try:
        counts = database.get_table_counts()
        return {
            "status": "success",
            "counts": counts,
        }
    except Exception as e:
        logger.error(f"Failed to get table counts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/reset/{table_name}")
async def reset_table(
    request: Request,
    table_name: str,
    user: CurrentUser = Depends(get_admin_user)
):
    """Reset (delete all rows) from a specific table. Admin only."""
    if table_name not in ALLOWED_RESET_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table. Allowed: {', '.join(sorted(ALLOWED_RESET_TABLES))}"
        )

    try:
        reset_map = {
            'employees': database.reset_employees,
            'genzai': database.reset_genzai,
            'ukeoi': database.reset_ukeoi,
            'staff': database.reset_staff,
            'yukyu_usage_details': database.reset_yukyu_usage_details,
        }

        # Get count before reset
        counts_before = database.get_table_counts()
        deleted_count = counts_before.get(table_name, 0)

        reset_map[table_name]()
        invalidate_employee_cache()

        await log_audit_action(
            request=request,
            action="RESET_TABLE",
            entity_type="data_management",
            entity_id=table_name,
            old_value={"count": deleted_count},
            user=user,
        )

        logger.info(f"Table '{table_name}' reset by {user.username} ({deleted_count} rows deleted)")

        return {
            "status": "success",
            "table": table_name,
            "deleted_count": deleted_count,
            "message": f"Table '{table_name}' reset successfully ({deleted_count} rows deleted)",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset table {table_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
